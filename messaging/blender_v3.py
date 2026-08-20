#!/usr/bin/env python3
"""
Blender Premium Logo v3 — Cinematic
- Brilliant cut gem with star facets
- 5-point HDRI-style lighting
- Gradient glass material with Fresnel
- Depth of field camera
- Poppins font for text
- 256 samples, Filmic, 2000x2000
"""
import bpy, bmesh, math, os, sys, json

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in [bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras]:
        for item in list(col):
            col.remove(item)

def hex_to_float(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def create_cut_gem():
    mesh = bpy.data.meshes.new("CutGem")
    obj = bpy.data.objects.new("CutGem", mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    n = 8
    r_out = 1.6
    r_mid = 1.0
    r_table = 0.6
    
    apex_top = bm.verts.new((0, 0, 0.95))
    
    table_verts = []
    for i in range(n):
        angle = (2 * math.pi * i) / n + math.pi/n
        table_verts.append(bm.verts.new((r_table * math.cos(angle), r_table * math.sin(angle), 0.85)))
    
    star_verts = []
    for i in range(n):
        angle = (2 * math.pi * i) / n
        star_verts.append(bm.verts.new((r_mid * math.cos(angle), r_mid * math.sin(angle), 0.55)))
    
    crown_verts = []
    for i in range(n):
        angle = (2 * math.pi * i) / n + math.pi/n
        crown_verts.append(bm.verts.new((r_out * math.cos(angle), r_out * math.sin(angle), 0.3)))
    
    girdle_verts = []
    for i in range(n):
        angle = (2 * math.pi * i) / n
        girdle_verts.append(bm.verts.new((r_out * math.cos(angle), r_out * math.sin(angle), 0)))
    
    pav_verts = []
    for i in range(n):
        angle = (2 * math.pi * i) / n + math.pi/n
        pav_verts.append(bm.verts.new((r_mid * math.cos(angle), r_mid * math.sin(angle), -0.35)))
    
    apex_bot = bm.verts.new((0, 0, -0.95))
    
    # Table
    bm.faces.new(table_verts)
    
    # Star facets
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([table_verts[i], star_verts[i], star_verts[j], table_verts[j]])
    
    # Crown facets
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([star_verts[i], crown_verts[i], crown_verts[j], star_verts[j]])
    
    # Girdle band
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([crown_verts[i], girdle_verts[i], girdle_verts[j], crown_verts[j]])
    
    # Pavilion facets
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([girdle_verts[i], pav_verts[i], pav_verts[j], girdle_verts[j]])
    
    # Pavilion to apex
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([apex_bot, pav_verts[j], pav_verts[i]])
    
    bm.to_mesh(mesh)
    bm.free()
    
    bpy.context.view_layer.objects.active = obj
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.025
    bevel.segments = 4
    bpy.ops.object.modifier_apply(modifier="Bevel")
    bpy.ops.object.shade_smooth()
    
    return obj

def create_premium_material(c1, c2, c3):
    mat = bpy.data.materials.new(name="PremiumGlass")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)
    
    glass = nodes.new('ShaderNodeBsdfGlass')
    glass.location = (300, 100)
    glass.inputs['Color'].default_value = (c1[0], c1[1], c1[2], 1.0)
    glass.inputs['Roughness'].default_value = 0.01
    glass.inputs['IOR'].default_value = 1.52
    
    glossy = nodes.new('ShaderNodeBsdfGlossy')
    glossy.location = (300, -100)
    glossy.inputs['Color'].default_value = (c2[0], c2[1], c2[2], 1.0)
    glossy.inputs['Roughness'].default_value = 0.03
    
    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (500, 0)
    
    fresnel = nodes.new('ShaderNodeFresnel')
    fresnel.location = (100, -100)
    fresnel.inputs['IOR'].default_value = 1.52
    
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (100, 200)
    ramp.color_ramp.elements[0].color = (c1[0], c1[1], c1[2], 1.0)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].color = (c3[0], c3[1], c3[2], 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements.new(0.5)
    ramp.color_ramp.elements[1].color = (c2[0], c2[1], c2[2], 1.0)
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-200, 200)
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (0, 200)
    
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], glass.inputs['Color'])
    links.new(ramp.outputs['Color'], glossy.inputs['Color'])
    links.new(fresnel.outputs['Fac'], mix.inputs['Fac'])
    links.new(glass.outputs['BSDF'], mix.inputs[1])
    links.new(glossy.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])
    
    return mat

def setup_lighting(c1, c2, c3):
    # Key
    key = bpy.data.lights.new(name="Key", type='AREA')
    key.energy = 1500
    key.size = 3
    key.color = (1.0, 0.98, 0.95)
    key_obj = bpy.data.objects.new("Key", key)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (4, -5, 7)
    key_obj.rotation_euler = (math.radians(25), math.radians(10), math.radians(30))
    
    # Fill
    fill = bpy.data.lights.new(name="Fill", type='AREA')
    fill.energy = 500
    fill.size = 6
    fill.color = (0.6, 0.8, 1.0)
    fill_obj = bpy.data.objects.new("Fill", fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (-5, -4, 5)
    fill_obj.rotation_euler = (math.radians(30), math.radians(-20), math.radians(-40))
    
    # Rim
    rim = bpy.data.lights.new(name="Rim", type='AREA')
    rim.energy = 800
    rim.size = 2
    rim.color = (c2[0], c2[1], c2[2])
    rim_obj = bpy.data.objects.new("Rim", rim)
    bpy.context.collection.objects.link(rim_obj)
    rim_obj.location = (-3, 5, 6)
    rim_obj.rotation_euler = (math.radians(-20), math.radians(10), math.radians(170))
    
    # Accent
    accent = bpy.data.lights.new(name="Accent", type='SPOT')
    accent.energy = 1000
    accent.spot_size = math.radians(40)
    accent.spot_blend = 0.3
    accent.color = (c3[0], c3[1], c3[2])
    accent_obj = bpy.data.objects.new("Accent", accent)
    bpy.context.collection.objects.link(accent_obj)
    accent_obj.location = (5, 4, 4)
    accent_obj.rotation_euler = (math.radians(55), 0, math.radians(-140))
    
    # Bottom fill
    bottom = bpy.data.lights.new(name="Bottom", type='AREA')
    bottom.energy = 200
    bottom.size = 4
    bottom.color = (c1[0], c1[1], c1[2])
    bottom_obj = bpy.data.objects.new("Bottom", bottom)
    bpy.context.collection.objects.link(bottom_obj)
    bottom_obj.location = (0, -3, -3)
    bottom_obj.rotation_euler = (math.radians(-45), 0, 0)
    
    # World gradient
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.02, 0.02, 0.04, 1.0)
    bg.inputs['Strength'].default_value = 0.5

def setup_camera():
    cam = bpy.data.cameras.new(name="Cam")
    cam.lens = 70
    cam.dof.use_dof = True
    cam.dof.focus_distance = 5.5
    cam.dof.aperture_fstop = 2.8
    cam_obj = bpy.data.objects.new("Camera", cam)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0, -5.5, 1.0)
    cam_obj.rotation_euler = (math.radians(80), 0, 0)
    bpy.context.scene.camera = cam_obj

def add_text(brand, tagline, c2):
    # Brand
    bpy.ops.object.text_add(location=(0, 0, -2.8))
    brand_obj = bpy.context.active_object
    brand_obj.data.body = brand
    brand_obj.data.align_x = 'CENTER'
    brand_obj.data.size = 0.65
    brand_obj.data.extrude = 0.02
    brand_obj.data.bevel_depth = 0.008
    brand_obj.data.bevel_resolution = 3
    
    font_path = "/opt/evolvixos/fonts/Poppins-ExtraBold.ttf"
    if os.path.exists(font_path):
        brand_obj.data.font = bpy.data.fonts.load(font_path)
    
    text_mat = bpy.data.materials.new(name="TextMat")
    text_mat.use_nodes = True
    bsdf = text_mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.98, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.15
    bsdf.inputs['Metallic'].default_value = 0.2
    brand_obj.data.materials.append(text_mat)
    
    # Tagline
    bpy.ops.object.text_add(location=(0, 0, -3.4))
    tag_obj = bpy.context.active_object
    tag_obj.data.body = tagline
    tag_obj.data.align_x = 'CENTER'
    tag_obj.data.size = 0.16
    
    tag_font_path = "/opt/evolvixos/fonts/Poppins-Medium.ttf"
    if os.path.exists(tag_font_path):
        tag_obj.data.font = bpy.data.fonts.load(tag_font_path)
    
    tag_mat = bpy.data.materials.new(name="TagMat")
    tag_mat.use_nodes = True
    tag_bsdf = tag_mat.node_tree.nodes['Principled BSDF']
    tag_bsdf.inputs['Base Color'].default_value = (c2[0], c2[1], c2[2], 1.0)
    tag_bsdf.inputs['Roughness'].default_value = 0.3
    tag_bsdf.inputs['Emission Color'].default_value = (c2[0], c2[1], c2[2], 1.0)
    tag_bsdf.inputs['Emission Strength'].default_value = 1.0
    tag_obj.data.materials.append(tag_mat)

def render_v3(brand, tagline, c1_hex, c2_hex, c3_hex, output_path):
    clear_scene()
    c1 = hex_to_float(c1_hex)
    c2 = hex_to_float(c2_hex)
    c3 = hex_to_float(c3_hex)
    
    gem = create_cut_gem()
    mat = create_premium_material(c1, c2, c3)
    gem.data.materials.append(mat)
    
    setup_lighting(c1, c2, c3)
    setup_camera()
    add_text(brand, tagline, c2)
    
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 256
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 2000
    scene.render.resolution_y = 2000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Medium High Contrast'
    scene.render.filepath = output_path
    
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED: {output_path}")

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    params = json.loads(argv[0]) if argv else {}
    render_v3(
        params.get('brand', 'Nexora'),
        params.get('tagline', 'BUILDING A SMARTER TOMORROW'),
        params.get('c1', '#0066FF'),
        params.get('c2', '#7C3AED'),
        params.get('c3', '#00CCFF'),
        params.get('output', '/tmp/v3_logo.png')
    )
