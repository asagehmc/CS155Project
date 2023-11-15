import numpy as np
import pyopencl as cl
import time
import pygame
from pygame.locals import *

# help from: https://github.com/PyOCL/pyopencl-examples

SCREEN_WIDTH = 100
SCREEN_HEIGHT = 100

OUTPUT_SIZE = SCREEN_HEIGHT * SCREEN_WIDTH

# Pygame initialization
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

if __name__ == '__main__':
    # vector struct
    vector_type = np.dtype([('x', np.float32), ('y', np.float32), ('z', np.float32)])

    # initialize triangle vertices (can be pointed to by multiple triangles)
    vertex_data = np.array([(0.0, -1, 1.0), (1.0, -1, 1.0), (1.0, -1, 0.0)],
                           dtype=vector_type)

    # triangle struct, 3 vertex indexes, 3 floats for normal vector, 1 material index
    triangle_type = np.dtype([('v1', np.uint32), ('v2', np.uint32), ('v3', np.uint32),
                              ('normal', vector_type),
                              ('mat', np.uint32)])

    # initialize triangle data, 3 indexes for vertices, 3 floats for normal vector, 1 material index
    triangle_data = np.array([(0, 1, 2, (0.0, 1.0, 0.0), 0)],
                             dtype=triangle_type)
    print(triangle_data)
    # light type struct
    light_type = np.dtype([('position', vector_type),
                           ("color", vector_type),
                           ('intensity', np.float32)])

    # initialize light data array
    light_data = np.array([((0.0, 0.5, 0.0), (1.0, 1.0, 1.0), 1.0)], dtype=light_type)

    # world data struct
    world_data_type = np.dtype([('num_tris', np.int32),
                                ('num_lights', np.int32),
                                ('world_ambient_color', vector_type),
                                ('world_ambient_intensity', np.float32)])

    # initialize world data
    world_data = np.array([(triangle_data.shape[0], light_data.shape[0],
                            (1, 1, 1), 1.0)], dtype=world_data_type)

    # -1 to 1 pixel position struct
    pixel_pos_type = np.dtype([('pix_x', np.float32), ('pix_y', np.float32)])

    # initialize pixel data array, an array of indexes for each pixel's position on the screen, starting at top right.
    frac = SCREEN_HEIGHT / SCREEN_WIDTH
    pix_data = np.array([(((i // SCREEN_WIDTH) + 0.5) / SCREEN_WIDTH * 2 - 1,
                          frac - ((i % SCREEN_WIDTH) + 0.5) / SCREEN_WIDTH * 2)
                         for i in range(SCREEN_WIDTH * SCREEN_HEIGHT)],
                        dtype=pixel_pos_type)

    # material struct
    material_type = np.dtype([('ambient_color', vector_type),
                              ('diffuse_color', vector_type),
                              ('specular_color', vector_type),
                              ('specular_power', np.int32)])

    material_data = np.array([((0.2, 0.2, 0.2), (0.6, 0.6, 0.6), (0.2, 0.2, 0.2), 30)], dtype=material_type)

    # camera data struct
    camera_data_type = np.dtype([('position', vector_type),
                                 ('right', vector_type),
                                 ('up', vector_type),
                                 ('forward', vector_type)])  # note: only including this cause it's faster to do once

    # initialize camera data array
    # position, right, up, forward
    camera_data = np.array([((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))],
                           dtype=camera_data_type)

    # load program from cl source file
    f = open('trace.cl', 'r', encoding='utf-8')
    kernels = ''.join(f.readlines())
    f.close()

    # prepare data
    matrix = np.random.randint(low=1, high=101, dtype=np.uint32, size=OUTPUT_SIZE)

    # prepare memory for final answer from OpenCL
    out = np.empty(shape=(SCREEN_WIDTH, SCREEN_HEIGHT, 3), dtype=np.uint8)

    # create context
    ctx = cl.create_some_context()

    # create command queue
    queue = cl.CommandQueue(ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)

    # prepare device memory for input
    triangle_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=triangle_data)
    vertex_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=vertex_data)
    light_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=light_data)
    camera_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=camera_data)
    material_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=material_data)
    pixel_pos_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=pix_data)
    world_data_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=world_data)

    # prepare device memory for output
    out_buf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, out.nbytes)

    # compile kernel code
    prg = cl.Program(ctx, kernels).build()
    time_kernel_compilation = time.time()

    # execute kernel programs
    evt = prg.trace_rays(queue, (OUTPUT_SIZE,), (1,), triangle_buf, vertex_buf, light_buf,
                         camera_buf, material_buf, pixel_pos_buf, world_data_buf, out_buf)
    # wait for kernel executions
    evt.wait()

    cl.enqueue_copy(queue, out, out_buf).wait()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        pygame.surfarray.blit_array(screen, out)
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
