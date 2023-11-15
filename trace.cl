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


void print(__constant char* str, __global char* debug_buf, int debug_id);

// this is a kind of a janky debug function, we can fix it later
// just don't write any $ signs in your debugging I guess.
// this will get really slow if we print out a lot at a time
void print(__constant char* str, __global char* debug_buf, int debug_id) {
    int DEBUG_ID = 4;

    if (debug_id != DEBUG_ID) {
        return;
    }
    int start = 0;
    // while string is $, move forwards
    while (debug_buf[start] != 36) {
        start += 1;
    }
    // while we're not at the end of the string, and not at the end of the debug_buf, copy chars over
    for (int i = 0; str[i] != 0 && debug_buf[start] != 0; ++i) {
        debug_buf[start] = str[i];
        ++start;
    }
    // if there is space, make a newline
    if (start != 0) {
        debug_buf[start] = 10;
    }
    free(str);
}

float vdot(__constant vector* v1, __constant vector* v2);

float vdot(__constant vector* v1, __constant vector* v2) {
    return v1->x * v2->x + v1->y + v2->y + v1->z * v2->z;
}

void vnormalize(__private vector* v);

void vnormalize(__private vector* v) {
    float mag = 1; //magnitude(v->x);
    v->x = v->x / mag;
    v->y = v->y / mag;
    v->z = v->z / mag;
}

float vmagnitude(__constant vector* v);

float vmagnitude(__constant vector* v) {
    return sqrt(v->x * v->x + v->y + v->y + v->z * v->z);
}

__kernel void trace_rays(__global triangle* tris,
                         __global vector* vertices,
                         __global light* lights,
                         __global camera_data* camera,
                         __global pixel_pos* pixels,
                         __global pixel_color* out,
                         __global char* debug) {

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
