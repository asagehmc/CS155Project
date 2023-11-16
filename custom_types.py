import numpy as np

# vector struct
vector_type = np.dtype([('x', np.float32), ('y', np.float32), ('z', np.float32)])

# triangle struct, 3 vertex indexes, 3 floats for normal vector, 1 material index
triangle_type = np.dtype([('v1', np.uint32), ('v2', np.uint32), ('v3', np.uint32),
                          ('mat', np.uint32)])

# light type struct
light_type = np.dtype([('position', vector_type),
                       ("color", vector_type),
                       ('intensity', np.float32)])

# world data struct
world_data_type = np.dtype([('num_tris', np.int32),
                            ('num_lights', np.int32),
                            ('world_ambient_color', vector_type),
                            ('world_background_color', vector_type),
                            ('world_ambient_intensity', np.float32)])

# -1 to 1 pixel position struct
pixel_pos_type = np.dtype([('pix_x', np.float32), ('pix_y', np.float32)])

# material struct
material_type = np.dtype([('ambient_color', vector_type),
                          ('diffuse_color', vector_type),
                          ('specular_color', vector_type),
                          ('specular_power', np.int32)])

# camera data struct
camera_data_type = np.dtype([('position', vector_type),
                             ('right', vector_type),
                             ('up', vector_type),
                             ('forward', vector_type)])  # note: only including this cause it's faster to do once
