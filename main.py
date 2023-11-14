import numpy as np
import pyopencl as cl
import time

# help from: https://github.com/PyOCL/pyopencl-examples

SCREEN_WIDTH = 3
SCREEN_HEIGHT = 3

INPUT_SIZE = 9
OUTPUT_SIZE = SCREEN_HEIGHT * SCREEN_WIDTH
if __name__ == '__main__':
    triangle_type = np.dtype([('v1', np.uint32), ('v2', np.uint32), ('v3', np.uint32),
                              ('normx', np.float32), ('normy', np.float32), ('normz', np.float32),
                              ('mat', np.uint32)])

    vertex_type = np.dtype([('x', np.float32), ('y', np.float32), ('z', np.float32)])

    light_type = np.dtype([('x', np.float32), ('y', np.float32), ('z', np.float32),
                           ('r', np.uint32), ('g', np.uint32), ('b', np.uint32),
                           ('intensity', np.float32)])

    pixel_pos_type = np.dtype([('pix_x', np.uint32), ('pix_y', np.uint32)])

    pixel_color_type = np.dtype([('r', np.uint32), ('g', np.uint32), ('b', np.uint32)])

    camera_data_type = np.dtype([('width', np.uint32), ('height', np.uint32),
                                 ('x', np.float32), ('y', np.float32), ('z', np.float32),
                                 ('x_dir', np.float32), ('y_dir', np.float32), ('z_dir', np.float32)])

    triangle_data = np.array([[0, 1, 2, 0.0, 0.0, -1.0, 1], [0, 3, 4, 0.0, 0.0, -1.0, 1]],
                             dtype=triangle_type)

    vertex_data = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [-1.0, 1.0, 1.0], [0.0, -1.0, 15.0], [1.0, -1.0, 1.0]],
                           dtype=vertex_type)

    # initialize pixel data array, an array of indexes for each pixel's position on the screen, starting at top right.
    # TODO: turn this into floating point -1 to 1
    pix_data = np.array([(i % SCREEN_WIDTH, i // SCREEN_HEIGHT) for i in range(SCREEN_WIDTH * SCREEN_HEIGHT)],
                        dtype=pixel_pos_type)

    # load program from cl source file
    f = open('trace.cl', 'r', encoding='utf-8')
    kernels = ''.join(f.readlines())
    f.close()

    # prepare data
    matrix = np.random.randint(low=1, high=101, dtype=np.uint32, size=INPUT_SIZE)
    print(matrix)
    # prepare memory for final answer from OpenCL
    out = np.empty(OUTPUT_SIZE, dtype=pixel_color_type)

    # create context
    ctx = cl.create_some_context()
    # create command queue
    queue = cl.CommandQueue(ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)

    # prepare device memory for input / output
    triangle_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=matrix)
    vertex_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=matrix)
    light_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=matrix)
    pixel_pos_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=matrix)

    out_buf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, out.nbytes)

    # compile kernel code
    prg = cl.Program(ctx, kernels).build()
    time_kernel_compilation = time.time()

    # execute kernel programs
    evt = prg.adjust_score(queue, (INPUT_SIZE,), (1,), triangle_buf, vertex_buf, light_buf, pixel_pos_buf, out_buf)
    # wait for kernel executions
    evt.wait()

    cl.enqueue_copy(queue, out, out_buf).wait()

    print(out)
