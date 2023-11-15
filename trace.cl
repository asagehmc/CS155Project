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
    float r;
    float g;
    float b;
} pixel_color;

typedef struct {
    vector position;
    vector right;
    vector up;
    vector forwards;
    float focal_dist;
} camera_data;

float vdot(__constant vector* v1, __constant vector* v2);
void vnormalize(__private vector* v);
float vmagnitude(__private vector* v);


float vdot(__constant vector* v1, __constant vector* v2) {
    return v1->x * v2->x + v1->y + v2->y + v1->z * v2->z;
}

float vmagnitude(__private vector* v) {
    return sqrt(v->x * v->x + v->y * v->y + v->z * v->z);
}

void vnormalize(__private vector* v) {
    float mag = vmagnitude(v);
    v->x = v->x / mag;
    v->y = v->y / mag;
    v->z = v->z / mag;
}

__kernel void trace_rays(__global triangle* tris,
                         __global vector* vertices,
                         __global light* lights,
                         __global camera_data* camera,
                         __global pixel_pos* pixels,
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
    vnormalize(&ray_dir);


    out[global_id].r = ray_dir.x;
    out[global_id].g = ray_dir.y;
    out[global_id].b = ray_dir.z;
}
