import pygame
from datetime import datetime
import pyopencl as cl
import time
from pygame.locals import *
from custom_types import *

# help from: https://github.com/PyOCL/pyopencl-examples
from world import World

FULLSCREEN = True
RESIZING = 3
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 300

OUTPUT_SIZE = SCREEN_HEIGHT * SCREEN_WIDTH

CAN_DIE = False

# Pygame initialization
pygame.init()

small_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
screen = None

if FULLSCREEN:
    screen = pygame.display.set_mode((SCREEN_WIDTH * RESIZING, SCREEN_HEIGHT * RESIZING), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((SCREEN_WIDTH * RESIZING, SCREEN_HEIGHT * RESIZING))

clock = pygame.time.Clock()
pygame.font.init()
font = pygame.font.SysFont('courier', 30)

if __name__ == '__main__':
    world = World()

    # initialize pixel data array, an array of indexes for each pixel's position on the screen, starting at top right.
    frac = SCREEN_HEIGHT / SCREEN_WIDTH
    pix_data = np.array([(((i // SCREEN_HEIGHT) + 0.5) / SCREEN_WIDTH * 2 - 1,
                          frac - ((i % SCREEN_HEIGHT) + 0.5) / SCREEN_WIDTH * 2)
                         for i in range(SCREEN_WIDTH * SCREEN_HEIGHT)],
                        dtype=pixel_pos_type)

    # load program from cl source file
    f = open('trace.cl', 'r', encoding='utf-8')
    kernels = ''.join(f.readlines())
    f.close()

    # prepare memory for final answer from OpenCL
    out = np.empty(shape=(SCREEN_WIDTH, SCREEN_HEIGHT, 3), dtype=np.uint8)

    # create context
    ctx = cl.create_some_context(interactive=False)

    # build program
    prg = cl.Program(ctx, kernels).build()

    # create command queue
    queue = cl.CommandQueue(ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)
    x = 0
    running = True
    while running:

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
        dt = 1/clock.get_fps() if clock.get_fps() > 0 else 0

        # set light position to move around player
        x += 2*dt
        player_pos = world.player.get_center()
        world.game_lights[0].set_position(player_pos[0] + 2*np.sin(x), player_pos[1] + 8, player_pos[2] + 2*np.cos(x) - 2)

        # prepare device memory for input
        rect_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=world.buf_wrap.rects)
        light_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=world.lights_buf)
        camera_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=world.camera_data_buf)
        material_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=world.materials_buf)
        pixel_pos_buf = cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=pix_data)
        world_data_buf = \
            cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=world.world_data_buf)
        bounding_volume_buf = \
            cl.Buffer(ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=world.buf_wrap.hierarchy)
        # prepare device memory for output
        out_buf = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, out.nbytes)
        # compile kernel code
        time_kernel_compilation = time.time()

        # execute kernel programs
        evt = prg.trace_rays(queue, (OUTPUT_SIZE,), (1,), rect_buf, light_buf, camera_buf,
                             material_buf, pixel_pos_buf, world_data_buf, out_buf, bounding_volume_buf)
        # wait for kernel executions
        world.update(dt)
        before = int(datetime.timestamp(datetime.now()) * 1000)
        if world.game_over:
            break
        evt.wait()

        cl.enqueue_copy(queue, out, out_buf).wait()
        pygame.surfarray.blit_array(small_screen, out)
        # text = str(int(clock.get_fps()))
        # text_surface = font.render(text, False, (255, 255, 255))
        # screen.blit(text_surface, (SCREEN_WIDTH-60, 10))

        resized_surface = pygame.transform.scale(small_screen, (SCREEN_WIDTH * RESIZING, SCREEN_HEIGHT * RESIZING))

        newSurface = pygame.transform.scale(small_screen, (SCREEN_WIDTH * RESIZING, SCREEN_HEIGHT * RESIZING))
        screen.blit(newSurface, (0, 0))
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
