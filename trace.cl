typedef struct {
    uint a;
    uint b;
    uint c;
    float normx;
    float normy;
    float normz;
    int mat;
} triangle_type;

typedef struct {
    float x;
    float y;
    float z;
} vertex_type;

typedef struct {
    float x;
    float y;
    float z;
    uint r;
    uint g;
    uint b;
    float intensity;
} light_type;

typedef struct {
    uint x;
    uint y;
} pixel_pos_type;

typedef struct {
    uint r;
    uint g;
    uint b;
} pixel_color_type;

__kernel void adjust_score(__global triangle_type* tris, __global vertex_type* vertices,
    __global light_type* lights, __global pixel_pos_type* pixels, __global pixel_color_type* out) {
    int global_id = get_global_id(0);

    out[global_id].r = global_id;
    out[global_id].g = 0;
    out[global_id].b = 0;
}