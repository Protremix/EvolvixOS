#!/usr/bin/env python3
"""
Blender Premium Logo Renderer v2 — Photorealistic
Enhanced: Faceted gem, 4-point lighting, gradient glass, glow, 2000x2000
"""
import bpy, bmesh, math, os, sys, json

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in [bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.textures]:
        for item in list(col):
            col.remove(item)

def hex_to_float(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def create_premium_gem():
    """Create a sophisticated faceted gem with multiple tiers"""
    mesh = bpy.data.meshes.new("PremiumGem")
    obj = bpy.data.objects.new("PremiumGem", mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    n = 8
    r_out = 1.6
    r_mid = 1.1
    
    # Vertices
    apex_top = bm.verts.new((0, 0, 1.0))
    
    crown1 = []
    for i in range(n):
        angle = (2 * math.pi * i) / n + math.pi/n
        crown1.append(bm.verts.new((r_out * math.cos(angle), r_out * math.sin(angle), 0.5)))
    
    crown2 = []
    for i in range(n):
        angle = (2 * math.pi * i) / n
        crown2.append(bm.verts.new((r_mid * math.cos(angle), r_mid * math.sin(angle), 0.2)))
    
    girdle = []
    for i in range(n):
        angle = (2 * math.pi * i) / n + math.pi/n
        girdle.append(bm.verts.new((r_out * math.cos(angle), r_out * math.sin(angle), 0)))
    
    pav1 = []
    for i in range(n):
        angle = (2 * math.pi * i) / n
        pav1.append(bm.verts.new((r_mid * math.cos(angle), r_mid * math.sin(angle), -0.3)))
    
    apex_bot = bm.verts.new((0, 0, -1.0))
    
    # Top crown (apex to crown1)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([apex_top, crown1[i], crown1[j]])
    
    # Crown1 to crown2
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([crown1[i], crown2[i], crown2[j], crown1[j]])
    
    # Crown2 to girdle
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([crown2[i], girdle[i], girdle[j], crown2[j]])
    
    # Girdle to pav1
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([girdle[i], pav1[i], pav1[j], girdle[j]])
    
    # Pavilion to apex_bot
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([apex_bot, pav1[j], pav1[i]])
    
    bm.to_mesh(mesh)
    bm.free()
    
    bpy.context.view_layer.objects.active = obj
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.03
    bevel.segments = 3
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
    output.location = (600, 0)
    
    glass = nodes.new('ShaderNodeBsdfGlass')
    glass.location = (200, 100)
    glass.inputs['Color'].default_value = (c1[0], c1[1], c1[2], 1.0)
    glass.inputs['Roughness'].default_value = 0.02
    glass.inputs['IOR'].default_value = 1.52
    
    glossy = nodes.new('ShaderNodeBsdfGlossy')
    glossy.location = (200, -100)
    glossy.inputs['Color'].default_value = (c2[0], c2[1], c2[2], 1.0)
    glossy.inputs['Roughness'].default_value = 0.05
    
    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (400, 0)
    
    fresnel = nodes.new('ShaderNodeFresnel')
    fresnel.location = (0, -100)
    fresnel.inputs['IOR'].default_value = 1.52
    
    # Color ramp for gradient
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (0, 200)
    ramp.color_ramp.elements[0].color = (c1[0], c1[1], c1[2], 1.0)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].color = (c3[0], c3[1], c3[2], 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements.new(0.5)
    ramp.color_ramp.elements[1].color = (c2[0], c2[1], c2[2], 1.0)
    
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-400, 200)
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-200, 200)
    
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], glass.inputs['Color'])
    links.new(ramp.outputs['Color'], glossy.inputs['Color'])
    links.new(fresnel.outputs['Fac'], mix.inputs['Fac'])
    links.new(glass.outputs['BSDF'], mix.inputs[1])
    links.new(glossy.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])
    
    return mat

def setup_premium_lighting(c1, c2, c3):
    # Key
    key = bpy.data.lights.new(name="Key", type='AREA')
    key.energy = 1200
    key.size = 2.5
    key.color = (1.0, 0.97, 0.93)
    key_obj = bpy.data.objects.new("Key", key)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (3, -4, 6)
    key_obj.rotation_euler = (math.radians(30), math.radians(15), math.radians(35))
    
    # Fill
    fill = bpy.data.lights.new(name="Fill", type='AREA')
    fill.energy = 400
    fill.size = 5
    fill.color = (0.7, 0.85, 1.0)
    fill_obj = bpy.data.objects.new("Fill", fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (-4, -3, 4)
    fill_obj.rotation_euler = (math.radians(35), math.radians(-25), math.radians(-45))
    
    # Rim
    rim = bpy.data.lights.new(name="Rim", type='AREA')
    rim.energy = 600
    rim.size = 1.5
    rim.color = (c2[0], c2[1], c2[2])
    rim_obj = bpy.data.objects.new("Rim", rim)
    bpy.context.collection.objects.link(rim_obj)
    rim_obj.location = (-2, 4, 5)
    rim_obj.rotation_euler = (math.radians(-25), math.radians(15), math.radians(160))
    
    # Accent spot
    accent = bpy.data.lights.new(name="Accent", type='SPOT')
    accent.energy = 800
    accent.spot_size = math.radians(45)
    accent.spot_blend = 0.5
    accent.color = (c3[0], c3[1], c3[2])
    accent_obj = bpy.data.objects.new("Accent", accent)
    bpy.context.collection.objects.link(accent_obj)
    accent_obj.location = (4, 3, 3)
    accent_obj.rotation_euler = (math.radians(60), 0, math.radians(-135))
    
    # World
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.02, 0.02, 0.04, 1.0)
    bg.inputs['Strength'].default_value = 0.3

def setup_camera():
    cam = bpy.data.cameras.new(name="Cam")
    cam.lens = 65
    cam_obj = bpy.data.objects.new("Camera", cam)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0, -5.5, 1.2)
    cam_obj.rotation_euler = (math.radians(78), 0, 0)
    bpy.context.scene.camera = cam_obj

def add_text(brand, tagline, c2):
    # Brand
    bpy.ops.object.text_add(location=(0, 0, -2.8))
    brand_obj = bpy.context.active_object
    brand_obj.data.body = brand
    brand_obj.data.align_x = 'CENTER'
    brand_obj.data.size = 0.7
    brand_obj.data.extrude = 0.015
    brand_obj.data.bevel_depth = 0.005
    brand_obj.data.bevel_resolution = 2
    
    text_mat = bpy.data.materials.new(name="TextMat")
    text_mat.use_nodes = True
    bsdf = text_mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.96, 0.96, 0.98, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.2
    bsdf.inputs['Metallic'].default_value = 0.15
    brand_obj.data.materials.append(text_mat)
    
    # Tagline
    bpy.ops.object.text_add(location=(0, 0, -3.5))
    tag_obj = bpy.context.active_object
    tag_obj.data.body = tagline
    tag_obj.data.align_x = 'CENTER'
    tag_obj.data.size = 0.18
    
    tag_mat = bpy.data.materials.new(name="TagMat")
    tag_mat.use_nodes = True
    tag_bsdf = tag_mat.node_tree.nodes['Principled BSDF']
    tag_bsdf.inputs['Base Color'].default_value = (c2[0], c2[1], c2[2], 1.0)
    tag_bsdf.inputs['Roughness'].default_value = 0.3
    tag_obj.data.materials.append(tag_mat)

def render_premium(brand, tagline, c1_hex, c2_hex, c3_hex, output_path):
    clear_scene()
    c1 = hex_to_float(c1_hex)
    c2 = hex_to_float(c2_hex)
    c3 = hex_to_float(c3_hex)
    
    gem = create_premium_gem()
    mat = create_premium_material(c1, c2, c3)
    gem.data.materials.append(mat)
    
    setup_premium_lighting(c1, c2, c3)
    setup_camera()
    add_text(brand, tagline, c2)
    
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 128
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
    render_premium(
        params.get('brand', 'Nexora'),
        params.get('tagline', 'BUILDING A SMARTER TOMORROW'),
        params.get('c1', '#0066FF'),
        params.get('c2', '#7C3AED'),
        params.get('c3', '#00CCFF'),
        params.get('output', '/tmp/premium_logo.png')
    )
