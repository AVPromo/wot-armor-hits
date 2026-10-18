# -*- coding: utf-8 -*-
"""Writes the hit line models of the mod into resources/content/sagtary_armor_hits/: for each color in COLORS,
line_<color>.model, .visual, .primitives and its texture .dds. Run with Python 2.7:
C:\\Python27\\python.exe tools\\make_line_model.py

A line is a tube 1 m long along its z axis from its origin and 1 m wide around it, with the client's glow shader
(shaders/std_effects/glow.fx, lit by itself, like the lines of the Battle Hits mod) and a texture of one color. The
mod stretches it onto a segment by its motor's matrix (views/hits/hit_lines.py).

The .primitives format of the engine: a magic number; the sections one after another, each padded to 4 bytes; a
table of the sections (size, 16 zero bytes, name length, name padded to 4 bytes) and the table's size at the end.
Section "vertices": the vertex format name in 64 bytes, the vertex count, the vertices (xyznuvtb: position, packed
normal, uv, packed tangent and binormal; 32 bytes). Section "indices": "list" in 64 bytes, the index count, the
group count, 16-bit indices, then the groups (first index, triangles, first vertex, vertices).
"""
import math
import os
import struct

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, 'resources', 'content',
                       'sagtary_armor_hits')
# The colors of the lines: name, (red, green, blue).
COLORS = (
    ('white', (255, 255, 255)),
    ('red', (255, 48, 32)),
)
SIDES = 8
MAGIC = 0x42a14e65


def packNormal(x, y, z):
    # 11 bits of x, 11 of y, 10 of z, signed.
    def bits(value, count, scale):
        return int(round(max(-1.0, min(1.0, value)) * scale)) & ((1 << count) - 1)
    return bits(x, 11, 1023) | bits(y, 11, 1023) << 11 | bits(z, 10, 511) << 22


def primitives():
    vertices, indices = [], []
    for side in range(SIDES + 1):
        angle = 2 * math.pi * side / SIDES
        nx, ny = math.cos(angle), math.sin(angle)
        for z in (0.0, 1.0):
            vertices.append(struct.pack('<3fI2fII', 0.5 * nx, 0.5 * ny, z, packNormal(nx, ny, 0.0), 0.5, 0.5,
                                        packNormal(0.0, 0.0, 1.0), packNormal(-ny, nx, 0.0)))
    for side in range(SIDES):
        a, b, c, d = side * 2, side * 2 + 1, side * 2 + 2, side * 2 + 3
        indices += [a, c, b, b, c, d]
    vertexData = 'xyznuvtb'.ljust(64, '\0') + struct.pack('<I', len(vertices)) + ''.join(vertices)
    indexData = ('list'.ljust(64, '\0') + struct.pack('<II', len(indices), 1) +
                 struct.pack('<%dH' % len(indices), *indices) +
                 struct.pack('<4i', 0, len(indices) // 3, 0, len(vertices)))
    body, table = struct.pack('<I', MAGIC), ''
    for name, data in (('vertices', vertexData), ('indices', indexData)):
        body += data + '\0' * (-len(data) % 4)
        table += struct.pack('<I', len(data)) + '\0' * 16 + struct.pack('<I', len(name)) + name
        table += '\0' * (-len(table) % 4)
    return body + table + struct.pack('<I', len(table))


def texture(rgb):
    # 4 x 4 pixels of the color, A8R8G8B8 without mipmaps.
    header = struct.pack('<4s7I', 'DDS ', 124, 0x100F, 4, 4, 16, 0, 0) + '\0' * 44
    pixelFormat = struct.pack('<2I4s5I', 32, 0x41, '\0\0\0\0', 32, 0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000)
    caps = struct.pack('<5I', 0x1000, 0, 0, 0, 0)
    red, green, blue = rgb
    return header + pixelFormat + caps + struct.pack('<4B', blue, green, red, 255) * 16


VISUAL = '''<%(name)s.visual>
   <node>
      <identifier>Scene Root</identifier>
      <transform>
         <row0>1.000000 0.000000 0.000000</row0>
         <row1>0.000000 1.000000 0.000000</row1>
         <row2>0.000000 0.000000 1.000000</row2>
         <row3>0.000000 0.000000 0.000000</row3>
      </transform>
   </node>
   <renderSet>
      <treatAsWorldSpaceObject>false</treatAsWorldSpaceObject>
      <node>Scene Root</node>
      <geometry>
         <vertices>vertices</vertices>
         <primitive>indices</primitive>
         <primitiveGroup>
            0
            <material>
               <identifier>line</identifier>
               <fx>shaders/std_effects/glow.fx</fx>
               <property>
                  doubleSided
                  <Bool>true</Bool>
               </property>
               <property>
                  diffuseMap
                  <Texture>%(resource)s.dds</Texture>
               </property>
            </material>
         </primitiveGroup>
      </geometry>
   </renderSet>
   <boundingBox>
      <min>-0.500000 -0.500000 0.000000</min>
      <max>0.500000 0.500000 1.000000</max>
   </boundingBox>
</%(name)s.visual>
'''

MODEL = '''<%(name)s.model>
   <nodelessVisual>%(resource)s</nodelessVisual>
</%(name)s.model>
'''


def main():
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    for color, rgb in COLORS:
        name = 'line_' + color
        values = {'name': name, 'resource': 'content/sagtary_armor_hits/' + name}
        # The HD client looks for the texture with the _hd suffix first.
        for extension, data in (('.primitives', primitives()), ('.dds', texture(rgb)), ('_hd.dds', texture(rgb)),
                                ('.visual', VISUAL % values), ('.model', MODEL % values)):
            path = os.path.join(OUT_DIR, name + extension)
            with open(path, 'wb') as f:
                f.write(data)
            print('write ' + os.path.normpath(path))


main()
