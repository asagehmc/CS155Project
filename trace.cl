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
    int num_tris;
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
    uint a;
    uint b;
    uint c;
    vector normal;
    int mat;
} triangle;

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
    vector v = {v1->x - v2->x, v1->y - v2->y, v1->z - v2->z};
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


__kernel void trace_rays(__global triangle* tris,
                         __global vector* vertices,
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
    int closest_triangle = -1;
    float closest_hit = INFINITY;
    // find closest triangle
    for (int i = 0; i < world->num_tris; ++i) {
        // if ray & plane are not parallel
        if (pgdot(&ray_dir, &(tris[i].normal)) != 0) {
            vector point_on_plane = (vertices[tris[i].a]);
            __private vector point_minus_direction = ppminus(&point_on_plane, &(ray_cast.pos));
            // calculate distance to plane
            float d = pgdot(&point_minus_direction, &(tris[i].normal)) /
                      pgdot(&(ray_cast.dir), &(tris[i].normal));
            // this is the new closest triangle
            if (d >= 0 && d < closest_hit) {
                closest_hit = d;
                closest_triangle = i;
            }
        }
    }
    // copy important data to __private scope
    triangle tri = tris[closest_triangle];
    material mat = materials[tri.mat];
    vector origin = camera->position;
    vector travel_vec = pCmult(&(ray_cast.dir), closest_hit);
    vector intersection_point = ppsum(&origin, &travel_vec);
    if (closest_triangle != -1) {
        //get ambient light
        vector ambient_and_world = gpmult(&(world->world_ambient_color), &(mat.ambient_color));
        vector light = pCmult(&ambient_and_world, world->world_ambient_intensity);
        //get ambient & spectral light
        for (int i = 0; i < world->num_lights; ++i) {
            // setup required vector data
            vector light_color = lights[i].color;
            vector light_pos = lights[i].position;
            vector to_light = ppminus(&light_pos, &intersection_point);
            pnormalize(&to_light);

            // get diffuse color
            vector diffuse = pCmult(&light_color, fmax(ppdot(&tri.normal, &to_light), 0));
            diffuse = ppmult(&mat.diffuse_color, &diffuse);

            // construct the reflection vector
            vector reflected = pCmult(&tri.normal, ppdot(&to_light, &tri.normal));
            reflected = pCmult(&reflected, 2);
            reflected = ppminus(&reflected, &to_light);

            vector specular = pCmult(&light_color, pow(fmax(-ppdot(&ray_cast.dir, &reflected), 0), mat.specular_power));
            specular = ppmult(&mat.diffuse_color, &specular);

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
