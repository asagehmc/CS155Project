typedef struct {
    float x;
    float y;
    float z;
} vector;

typedef struct {
    vector pos;
    vector dir;
} ray;

typedef struct {
    int num_rects;
    int bounding_hierarchy_size;
    int bounding_hierarchy_height;
    int num_lights;
    vector world_ambient_color;
    vector world_background_color;
    float world_ambient_intensity;
} world_data;

typedef struct {
    vector ambient_color;
    vector diffuse_color;
    vector specular_color;
    int specular_power;
} material;


typedef struct {
    vector bot;
    vector top;
    vector normal;
    uint mat;
} rect;

typedef struct {
    vector position;
    vector color;
    float intensity;
} light;

typedef struct {
    float x;
    float y;
} pixel_pos;

typedef struct {
    char r;
    char g;
    char b;
} pixel_color;

typedef struct {
    vector position;
    vector right;
    vector up;
    vector forwards;
    float focal_dist;
} camera_data;

typedef struct {
    int initialized;
    vector top;
    vector bottom;
    int plane1;
    int plane2;
    int same;
} bounding_node;

typedef struct {
    float distance;
    int closest_rect;
} closest_hit_data;

float ppdot(__private vector* v1, __private vector* v2);
float pgdot(__private vector* v1, __global vector* v2);
vector ppminus(__private vector* v1, __private vector* v2);
void pnormalize(__private vector* v);
float pmagnitude(__private vector* v);
vector gpmult(__global vector* v1, __private vector* v2);
vector ppmult(__private vector* v1, __private vector* v2);
vector pCmult(__private vector* v1, float f);
vector ppsum(__private vector* v1, __private vector* v2);
closest_hit_data get_closest_hit(int index, __global bounding_node* tree, int tree_size, int tree_height,
                                 __global rect* rects, __private ray* ray_cast);
closest_hit_data check_intersection(__global rect* rects, int index, __private ray* ray_cast);
bool intersects_box(__global bounding_node* box, __private ray* ray_cast);


float ppdot(__private vector* v1, __private vector* v2) {
    return v1->x * v2->x + v1->y * v2->y + v1->z * v2->z;
}
float pgdot(__private vector* v1, __global vector* v2) {
    return v1->x * v2->x + v1->y * v2->y + v1->z * v2->z;
}

float pmagnitude(__private vector* v) {
    return sqrt(v->x * v->x + v->y * v->y + v->z * v->z);
}

void pnormalize(__private vector* v) {
    float mag = pmagnitude(v);
    v->x = v->x / mag;
    v->y = v->y / mag;
    v->z = v->z / mag;
}

vector ppminus(__private vector* v1, __private vector* v2) {
    __private vector v = {v1->x - v2->x, v1->y - v2->y, v1->z - v2->z};
    return v;
}

vector gpmult(__global vector* v1, __private vector* v2) {
    __private vector v = {v1->x * v2->x, v1->y * v2->y, v1->z * v2->z};
    return v;
}

vector ppmult(__private vector* v1, __private vector* v2) {
    __private vector v = {v1->x * v2->x, v1->y * v2->y, v1->z * v2->z};
    return v;
}

vector pCmult(__private vector* v, float f) {
    __private vector vout = {v->x * f, v->y * f, v->z * f};
    return vout;
}

vector ppsum(__private vector* v1, __private vector* v2) {
    __private vector vout = {v1->x + v2->x, v1->y + v2->y, v1->z + v2->z};
    return vout;
}

closest_hit_data check_intersection(__global rect* rects, int index, __private ray* ray_cast) {
    vector top = rects[index].top;
    vector bot = rects[index].bot;
    vector normal = rects[index].normal;
    //if we are parallel, or backface is showing, skip rect
    if (ppdot(&(ray_cast->dir), &normal) < 0) {
        vector point_minus_direction = ppminus(&bot, &(ray_cast->pos));
        // calculate distance to plane
        float d = ppdot(&point_minus_direction, &normal) /
                  ppdot(&(ray_cast->dir), &normal);
        if (d >= 0) {
            vector travel_vec = pCmult(&(ray_cast->dir), d);
            vector intersection_point = ppsum(&(ray_cast->pos), &travel_vec);
            float bot1;
            float bot2;
            float top1;
            float top2;
            float intersect1;
            float intersect2;
            if (normal.x != 0) {
                bot1 = bot.y;
                bot2 = bot.z;
                top1 = top.y;
                top2 = top.z;
                intersect1 = intersection_point.y;
                intersect2 = intersection_point.z;
            } else if (normal.y != 0) {
                bot1 = bot.x;
                bot2 = bot.z;
                top1 = top.x;
                top2 = top.z;
                intersect1 = intersection_point.x;
                intersect2 = intersection_point.z;
            } else {
                bot1 = bot.x;
                bot2 = bot.y;
                top1 = top.x;
                top2 = top.y;
                intersect1 = intersection_point.x;
                intersect2 = intersection_point.y;
            }
            if (bot1 < intersect1 && intersect1 < top1 && bot2 < intersect2 && intersect2 < top2) {
                closest_hit_data out = {d, index};
                return out;
            }
        }
    }
    closest_hit_data out = {INFINITY, -1};
    return out;
}

// credit to chatgpt
bool intersects_box(__global bounding_node* box, __private ray* ray_cast) {
    // printf("box_data: %d, %d\n", box->initialized, box->same);
    // printf("low: %f, %f, %f\n", box->bottom.x, box->bottom.y, box->bottom.z);
    // printf("high: %f, %f, %f\n", box->top.x, box->top.y, box->top.z);


    // Check if the ray is parallel to the axes
    if (ray_cast->dir.x == 0.0) {
        if (ray_cast->pos.x < box->bottom.x || ray_cast->pos.x > box->top.x) {
            return false;
        }
    }

    if (ray_cast->dir.y == 0.0f) {
        if (ray_cast->pos.y < box->bottom.y || ray_cast->pos.y > box->top.y) {
            return false;
        }
    }

    if (ray_cast->dir.z == 0.0f) {
        if (ray_cast->pos.z < box->bottom.z || ray_cast->pos.z > box->top.z) {
            return false;
        }
    }

    float invDirX = (ray_cast->dir.x != 0.0f) ? 1.0f / ray_cast->dir.x : INFINITY;
    float invDirY = (ray_cast->dir.y != 0.0f) ? 1.0f / ray_cast->dir.y : INFINITY;
    float invDirZ = (ray_cast->dir.z != 0.0f) ? 1.0f / ray_cast->dir.z : INFINITY;



    float tMinX = (box->bottom.x - ray_cast->pos.x) * invDirX;
    float tMaxX = (box->top.x - ray_cast->pos.x) * invDirX;
    // printf("x_low: %f %f %f =  %f\n", box->bottom.x, ray_cast->pos.x, invDirX, tMinX);
    // printf("x_high: %f %f %f = %f\n", box->top.x, ray_cast->pos.x, invDirX, tMaxX);



    if (tMinX > tMaxX) {
        float temp = tMinX;
        tMinX = tMaxX;
        tMaxX = temp;
    }

    float tMinY = (box->bottom.y - ray_cast->pos.y) * invDirY;
    float tMaxY = (box->top.y - ray_cast->pos.y) * invDirY;

    if (tMinY > tMaxY) {
        float temp = tMinY;
        tMinY = tMaxY;
        tMaxY = temp;
    }

    float tMinZ = (box->bottom.z - ray_cast->pos.z) * invDirZ;
    float tMaxZ = (box->top.z - ray_cast->pos.z) * invDirZ;

    if (tMinZ > tMaxZ) {
        float temp = tMinZ;
        tMinZ = tMaxZ;
        tMaxZ = temp;
    }
    // printf("ray_cast: %f, %f, %f\n", ray_cast->dir.x, ray_cast->dir.y, ray_cast->dir.z);
    // printf("tMins: %f, %f, %f\n\n", tMinX, tMinY, tMinZ);

    float tMin = tMinX > tMinY ? tMinX : tMinY;
    tMin = tMin > tMinZ ? tMin : tMinZ;

    float tMax = tMaxX < tMaxY ? tMaxX : tMaxY;
    tMax = tMax < tMaxZ ? tMax : tMaxZ;
    return tMin <= tMax;

}

closest_hit_data get_closest_hit(int i,
                                 __global bounding_node* tree,
                                 int tree_size,
                                 int tree_height,
                                 __global rect* rects,
                                 __private ray* ray_cast) {
    int index = 0;
    int prev_index = -1;
    int current_depth = 0;
    closest_hit_data out = {INFINITY, -1};


    while (index != tree_size) {

        if (prev_index == index * 2 + 2 //if we are coming from a right branch
            || index >= tree_size // we are outside of tree
            || !tree[index].initialized // we are in uninitialized node of array for tree
            || (!tree[index].same
                && !intersects_box(&(tree[index]), ray_cast))) // we are missed by ray cast
        {
            prev_index = index;
            index = (index - 1) / 2; //step back up the tree
            --current_depth;
            continue;
        }
        // check planes if they are present, but only the first time through
        if (tree[index].plane1 != -1 && prev_index < index) {
            closest_hit_data plane1 = check_intersection(rects, tree[index].plane1, ray_cast);
            if (out.distance > plane1.distance) {
                out = plane1;
            }
        }
        if (tree[index].plane2 != -1 && prev_index < index) {
            closest_hit_data plane2 = check_intersection(rects, tree[index].plane2, ray_cast);
            if (out.distance > plane2.distance) {
                out = plane2;
            }
        }
        if (prev_index < index) { //if coming from a parent node, we go left
            prev_index = index;
            index = index * 2 + 1;
        } else if (prev_index == index * 2 + 1) { //if coming from a left node, go right
            prev_index = index;
            index = index * 2 + 2;
        }

    }
    return out;
}



__kernel void trace_rays(__global rect* rects,
                         __global light* lights,
                         __global camera_data* camera,
                         __global material* materials,
                         __global pixel_pos* pixels,
                         __global world_data* world,
                         __global pixel_color* out,
                         __global bounding_node* bounding_hierarchy
                        ) {

    __private int global_id = get_global_id(0);
    __private pixel_pos screen_coords = pixels[global_id];
    // forwards vector
    __private vector f = camera->forwards;
    // right vector
    __private vector u = camera->up;
    // up vector
    __private vector r = camera->right;


    // initialize ray
    __private vector ray_dir = {f.x + u.x * screen_coords.y + r.x * screen_coords.x,
                      f.y + u.y * screen_coords.y + r.y * screen_coords.x,
                      f.z + u.z * screen_coords.y + r.z * screen_coords.x
                     };
    pnormalize(&ray_dir);
    __private ray ray_cast = {camera->position, ray_dir};

    // find closest triangle
    vector origin = camera->position;
    closest_hit_data hit = get_closest_hit(0, bounding_hierarchy,
                                           world->bounding_hierarchy_size, world->bounding_hierarchy_height,
                                           rects, &ray_cast);
//
//    // index for the closest rectangle hit
//    int closest_rect = hit.closest_rect;
//    float closest_hit = hit.distance;

//    if (closest_rect != -1) {
//        // copy important data to __private scope
//        rect rectangle = rects[closest_rect];
//        vector normal = rectangle.normal;
//        material mat = materials[rectangle.mat];
//
//        vector travel_vec = pCmult(&(ray_cast.dir), closest_hit);
//        vector intersection_point = ppsum(&origin, &travel_vec);
//
//        //get ambient light
//        vector ambient_and_world = gpmult(&(world->world_ambient_color), &(mat.ambient_color));
//        vector light = pCmult(&ambient_and_world, world->world_ambient_intensity);
//        //get ambient & specular light
//        for (int i = 0; i < world->num_lights; ++i) {
//            // setup required vector data
//            vector light_color = lights[i].color;
//            vector light_pos = lights[i].position;
//            vector to_light = ppminus(&light_pos, &intersection_point);
//            pnormalize(&to_light);
//
//            // get diffuse color
//            vector diffuse = pCmult(&light_color, fmax(ppdot(&normal, &to_light), 0));
//            diffuse = ppmult(&mat.diffuse_color, &diffuse);
//
//            // construct the reflection vector
//            vector reflected = pCmult(&normal, ppdot(&to_light, &normal));
//            reflected = pCmult(&reflected, 2);
//            reflected = ppminus(&reflected, &to_light);
//
//            vector specular = pCmult(&light_color, pow(fmax(-ppdot(&ray_cast.dir, &reflected), 0), mat.specular_power));
//            specular = ppmult(&mat.specular_color, &specular);
//
//            light = ppsum(&diffuse, &light);
//            light = ppsum(&specular, &light);
//        }
//        out[global_id].r = fmin(light.x, 1) * 255;
//        out[global_id].g = fmin(light.y, 1) * 255;
//        out[global_id].b = fmin(light.z, 1) * 255;
//        return;
//    }
//    out[global_id].r = world->world_background_color.x * 255;
//    out[global_id].g = world->world_background_color.y * 255;
//    out[global_id].b = world->world_background_color.z * 255;
}
