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

__kernel void adjust_score(__global triangle_type* tris,
                           __global vector_type* vertices,
                           __global light_type* lights,
                           __global camera_data_type* camera,
                           __global pixel_pos_type* pixels,
                           __global pixel_color_type* out) {
    int global_id = get_global_id(0);

    out[global_id].r = global_id;
    out[global_id].g = 0;
    out[global_id].b = 0;
}