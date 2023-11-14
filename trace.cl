typedef struct {
    float x;
    float y;
    float z;
} vector_type;

typedef struct {
    uint a;
    uint b;
    uint c;
    vector_type normal;
    int mat;
} triangle_type;

typedef struct {
    vector_type position;
    uint r;
    uint g;
    uint b;
    float intensity;
} light_type;

typedef struct {
    float x;
    float y;
} pixel_pos_type;

typedef struct {
    uint r;
    uint g;
    uint b;
} pixel_color_type;

typedef struct {
    vector_type position;
    vector_type right;
    vector_type up;
} camera_data_type;

void print(__constant char* str, __global char* debug_buf, int debug_id);

// this is a kind of a janky debug function, we can fix it later
// just dont write any $ signs in your debugging I guess.
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
}



__kernel void trace_rays(__global triangle_type* tris,
                         __global vector_type* vertices,
                         __global light_type* lights,
                         __global camera_data_type* camera,
                         __global pixel_pos_type* pixels,
                         __global pixel_color_type* out,
                         __global char* debug) {

    int global_id = get_global_id(0);

    print("Abcdef", debug, global_id);


    out[global_id].r = global_id;
    out[global_id].g = 0;
    out[global_id].b = 0;
}
