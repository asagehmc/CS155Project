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

float ppdot(__private vector* v1, __private vector* v2);
float pgdot(__private vector* v1, __global vector* v2);
vector ppminus(__private vector* v1, __private vector* v2);
void pnormalize(__private vector* v);
float pmagnitude(__private vector* v);
vector gpmult(__global vector* v1, __private vector* v2);
vector ppmult(__private vector* v1, __private vector* v2);
vector pCmult(__private vector* v1, float f);
vector ppsum(__private vector* v1, __private vector* v2);
bool barycentricInside(__private vector* point, __private vector* A, __private vector* B, __private vector* C);



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



__kernel void trace_rays(__global rect* rects,
                         __global light* lights,
                         __global camera_data* camera,
                         __global material* materials,
                         __global pixel_pos* pixels,
                         __global world_data* world,
                         __global pixel_color* out
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
    int closest_rect = -1;
    float closest_hit = INFINITY;
    // find closest triangle
    vector origin = camera->position;
    for (int i = 0; i < world->num_rects; ++i) {
        // if ray & plane are not parallel
        vector top = rects[i].top;
        vector bot = rects[i].bot;
        vector normal = rects[i].normal;

        //if we are parallel, or backface is showing, skip rect
        if (ppdot(&ray_dir, &normal) < 0) {
            vector point_minus_direction = ppminus(&bot, &(ray_cast.pos));
            // calculate distance to plane
            float d = ppdot(&point_minus_direction, &normal) /
                      ppdot(&(ray_cast.dir), &normal);
            //  this is the new closest rect?
            if (d >= 0 && d < closest_hit) {
                vector travel_vec = pCmult(&(ray_cast.dir), d);
                vector intersection_point = ppsum(&origin, &travel_vec);
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
                    closest_hit = d;
                    closest_rect = i;
                }

            }
        }
    }

    if (closest_rect != -1) {
        // copy important data to __private scope
        rect rectangle = rects[closest_rect];
        vector normal = rectangle.normal;
        material mat = materials[rectangle.mat];

        vector travel_vec = pCmult(&(ray_cast.dir), closest_hit);
        vector intersection_point = ppsum(&origin, &travel_vec);

        //get ambient light
        vector ambient_and_world = gpmult(&(world->world_ambient_color), &(mat.ambient_color));
        vector light = pCmult(&ambient_and_world, world->world_ambient_intensity);
        //get ambient & specular light
        for (int i = 0; i < world->num_lights; ++i) {
            // setup required vector data
            vector light_color = lights[i].color;
            vector light_pos = lights[i].position;
            vector to_light = ppminus(&light_pos, &intersection_point);
            pnormalize(&to_light);

            // get diffuse color
            vector diffuse = pCmult(&light_color, fmax(ppdot(&normal, &to_light), 0));
            diffuse = ppmult(&mat.diffuse_color, &diffuse);

            // construct the reflection vector
            vector reflected = pCmult(&normal, ppdot(&to_light, &normal));
            reflected = pCmult(&reflected, 2);
            reflected = ppminus(&reflected, &to_light);

            vector specular = pCmult(&light_color, pow(fmax(-ppdot(&ray_cast.dir, &reflected), 0), mat.specular_power));
            specular = ppmult(&mat.specular_color, &specular);

            light = ppsum(&diffuse, &light);
            light = ppsum(&specular, &light);
        }
        out[global_id].r = fmin(light.x, 1) * 255;
        out[global_id].g = fmin(light.y, 1) * 255;
        out[global_id].b = fmin(light.z, 1) * 255;
        return;
    }
    out[global_id].r = world->world_background_color.x * 255;
    out[global_id].g = world->world_background_color.y * 255;
    out[global_id].b = world->world_background_color.z * 255;
}
