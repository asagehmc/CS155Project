import numpy as np
import pyopencl as cl
import time

# help from: https://github.com/PyOCL/pyopencl-examples

SCREEN_WIDTH = 3
SCREEN_HEIGHT = 3

INPUT_SIZE = 9
OUTPUT_SIZE = SCREEN_HEIGHT * SCREEN_WIDTH
if __name__ == '__main__':
    # vector struct
    vector_type = np.dtype([('x', np.float32), ('y', np.float32), ('z', np.float32)])

    # triangle struct, 3 vertex indexes, 3 floats for normal vector, 1 material index
    triangle_type = np.dtype([('v1', np.uint32), ('v2', np.uint32), ('v3', np.uint32),
                              ('normal', vector_type),
                              ('mat', np.uint32)])

    # light type struct
    light_type = np.dtype([('position', vector_type),
                           ('r', np.uint32), ('g', np.uint32), ('b', np.uint32),
                           ('intensity', np.float32)])

    # -1 to 1 pixel position struct
    pixel_pos_type = np.dtype([('pix_x', np.float32), ('pix_y', np.float32)])

    # output pixel color struct
    pixel_color_type = np.dtype([('r', np.uint32), ('g', np.uint32), ('b', np.uint32)])

    # camera data struct
    camera_data_type = np.dtype([('position', vector_type),
                                 ('right', vector_type),
                                 ('up', vector_type)])

    # initialize triangle data, 3 indexes for vertices, 3 floats for normal vector, 1 material index
    triangle_data = np.array([(0, 1, 2, (0.0, 0.0, -1.0), 1), (0, 3, 4, (0.0, 0.0, -1.0), 1)],
                             dtype=triangle_type)

    # initialize triangle vertices (can be pointed to by multiple triangles)
    vertex_data = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [-1.0, 1.0, 1.0], [0.0, -1.0, 15.0], [1.0, -1.0, 1.0]],
                           dtype=vector_type)

    # initialize pixel data array, an array of indexes for each pixel's position on the screen, starting at top right.
    pix_data = np.array([(((i % SCREEN_WIDTH) + 0.5) / SCREEN_WIDTH * 2 - 1,
                          ((i // SCREEN_HEIGHT) + 0.5) / SCREEN_WIDTH * 2 - 1)
                         for i in range(SCREEN_WIDTH * SCREEN_HEIGHT)],
                        dtype=pixel_pos_type)

    # initialize light data array
    light_data = np.array([((0.0, 0.5, 0.0), 255, 255, 255, 1.0)], dtype=light_type)

    # initialize camera data array
    camera_data = np.array([((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))], dtype=camera_data_type)

    # load program from cl source file
    f = open('trace.cl', 'r', encoding='utf-8')
    kernels = ''.join(f.readlines())
    f.close()

    # prepare data
    matrix = np.random.randint(low=1, high=101, dtype=np.uint32, size=INPUT_SIZE)

    # prepare memory for final answer from OpenCL
    out = np.empty(OUTPUT_SIZE, dtype=pixel_color_type)

    # create context
    ctx = cl.create_some_context()
    # create command queue
    queue = cl.CommandQueue(ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)

    # prepare device memory for input
    triangle_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=vertex_data)
    vertex_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=pix_data)
    light_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=light_data)
    camera_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=camera_data)
    pixel_pos_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=pix_data)
    # prepare device memory for output
    out_buf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, out.nbytes)

    # compile kernel code
    prg = cl.Program(ctx, kernels).build()
    time_kernel_compilation = time.time()

    # execute kernel programs
    evt = prg.adjust_score(queue, (INPUT_SIZE,), (1,), triangle_buf, vertex_buf, light_buf,
                           camera_buf, pixel_pos_buf, out_buf)
    # wait for kernel executions
    evt.wait()

    cl.enqueue_copy(queue, out, out_buf).wait()

    print(out)
