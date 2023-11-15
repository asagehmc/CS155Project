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
    float world_ambient_intensity;
} world_data;

typedef struct {
    uint a;
    uint b;
    uint c;
    vector normal;
    int mat;
} triangle;

typedef struct {
    vector position;
    float r;
    float g;
    float b;
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

vector gpminus(__global vector* v1, __private vector* v2);
void pnormalize(__private vector* v);
float pmagnitude(__private vector* v);



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

vector gpminus(__global vector* v1, __private vector* v2) {
    vector v = {v1->x - v2->x, v1->y - v2->y, v1->z - v2->z};
    return v;
}


__kernel void trace_rays(__global triangle* tris,
                         __global vector* vertices,
                         __global light* lights,
                         __global camera_data* camera,
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
    for (int i = 0; i < world->num_tris; ++i) {
        // if ray & plane are not parallel
        if (pgdot(&ray_dir, &(tris[i].normal)) != 0) {
            __private vector point_minus_direction = gpminus(&(vertices[tris[i].a]), &(ray_cast.pos));
            float d = pgdot(&point_minus_direction, &(tris[i].normal)) /
                      pgdot(&(ray_cast.dir), &(tris[i].normal));

            if (d >= 0 && d < closest_hit) {
                closest_hit = d;
                closest_triangle = 1;
            }
        }
    }
    //__global vector v1_global = ;
    //__private vector v1 = {v1_global.x, v1_global.y, v1_global.z};
    if (closest_triangle != -1) {
        out[global_id].r = 255;
        out[global_id].g = 255;
        out[global_id].b = 255;
    }



}
