#!/usr/bin/env python3
"""
Blender 3D Logo Renderer — Premium Photorealistic
Creates 3D logo with real glass material, studio lighting, and PBR rendering.
"""
import bpy, bmesh, math, os, sys, json

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in [bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras]:
        for item in col:
            col.remove(item)

def create_gem_geometry(depth=0.4):
    """Create a hexagonal gem with faceted top and bottom"""
    # Top hexagon
    verts_top = []
    verts_bot = []
    verts_mid = []
    
    radius = 1.5
    n = 6
    for i in range(n):
        angle = (2 * math.pi * i) / n + math.pi/2
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        verts_top.append((x, y, depth * 0.5))
        verts_bot.append((x, y, -depth * 0.5))
        verts_mid.append((x * 0.6, y * 0.6, 0))
    
    # Add center vertices
    verts = [vert for pair in zip(verts_top, verts_bot) for vert in pair]
    verts.append((0, 0, depth * 0.8))  # top apex
    verts.append((0, 0, -depth * 0.8))  # bottom apex
    verts.extend([(x*0.6, y*0.6, 0) for x,y in [(radius*math.cos(a), radius*math.sin(a)) for a in [(2*math.pi*i)/n + math.pi/2 for i in range(n)]]])
    
    # Build mesh
    mesh = bpy.data.meshes.new("Gem")
    obj = bpy.data.objects.new("Gem", mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    # Create vertices
    bv_top = [bm.verts.new(v) for v in verts_top]
    bv_bot = [bm.verts.new(v) for v in verts_bot]
    bv_apex_top = bm.verts.new((0, 0, depth * 0.8))
    bv_apex_bot = bm.verts.new((0, 0, -depth * 0.8))
    
    # Top faces (triangles from apex to top hex)
    for i in range(n):
        bm.faces.new([bv_apex_top, bv_top[i], bv_top[(i+1) % n]])
    
    # Bottom faces
    for i in range(n):
        bm.faces.new([bv_apex_bot, bv_bot[(i+1) % n], bv_bot[i]])
    
    # Side faces (quads)
    for i in range(n):
        bm.faces.new([bv_top[i], bv_bot[i], bv_bot[(i+1) % n], bv_top[(i+1) % n]])
    
    bm.to_mesh(mesh)
    bm.free()
    
    # Add bevel for smooth edges
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.05
    bevel.segments = 4
    
    # Smooth shading
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier="Bevel")
    
    # Add subdivision for smoother
    subsurf = obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 3
    
    return obj

def create_glass_material(color1, color2, color3):
    """Create a premium glass-like material with gradient colors"""
    mat = bpy.data.materials.new(name="GlassPremium")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # Glass BSDF
    glass = nodes.new('ShaderNodeBsdfGlass')
    glass.location = (0, 0)
    glass.inputs['Color'].default_value = (color1[0], color1[1], color1[2], 1.0)
    glass.inputs['Roughness'].default_value = 0.05
    glass.inputs['IOR'].default_value = 1.45
    
    # Mix with Glossy for premium look
    glossy = nodes.new('ShaderNodeBsdfGlossy')
    glossy.location = (0, -150)
    glossy.inputs['Color'].default_value = (color2[0], color2[1], color2[2], 1.0)
    glossy.inputs['Roughness'].default_value = 0.1
    
    # Mix shader
    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (200, 0)
    mix.inputs['Fac'].default_value = 0.3
    
    # Fresnel for edge highlights
    fresnel = nodes.new('ShaderNodeFresnel')
    fresnel.location = (-200, -150)
    fresnel.inputs['IOR'].default_value = 1.45
    
    # Color ramp for gradient
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (-200, 100)
    ramp.color_ramp.elements[0].color = (color1[0], color1[1], color1[2], 1.0)
    ramp.color_ramp.elements[1].color = (color3[0], color3[1], color3[2], 1.0)
    
    # Geometry/Normal for gradient mapping
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 100)
    
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (-400, 100)
    
    # Links
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], glass.inputs['Color'])
    links.new(fresnel.outputs['Fac'], mix.inputs['Fac'])
    links.new(glass.outputs['BSDF'], mix.inputs[1])
    links.new(glossy.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])
    
    return mat

def setup_lighting():
    """Three-point studio lighting"""
    # Key light (warm, strong)
    key = bpy.data.lights.new(name="Key", type='AREA')
    key.energy = 800
    key.size = 3
    key.color = (1.0, 0.95, 0.9)
    key_obj = bpy.data.objects.new("Key", key)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (3, -3, 5)
    key_obj.rotation_euler = (math.radians(35), math.radians(20), math.radians(45))
    
    # Fill light (cool, soft)
    fill = bpy.data.lights.new(name="Fill", type='AREA')
    fill.energy = 300
    fill.size = 4
    fill.color = (0.7, 0.8, 1.0)
    fill_obj = bpy.data.objects.new("Fill", fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (-3, -2, 3)
    fill_obj.rotation_euler = (math.radians(40), math.radians(-30), math.radians(-45))
    
    # Rim light (colored, back)
    rim = bpy.data.lights.new(name="Rim", type='AREA')
    rim.energy = 500
    rim.size = 2
    rim.color = (0.6, 0.5, 1.0)
    rim_obj = bpy.data.objects.new("Rim", rim)
    bpy.context.collection.objects.link(rim_obj)
    rim_obj.location = (0, 3, 4)
    rim_obj.rotation_euler = (math.radians(-30), 0, 0)
    
    # World background
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.03, 0.03, 0.06, 1.0)
    bg.inputs['Strength'].default_value = 0.5

def setup_camera():
    cam = bpy.data.cameras.new(name="Camera")
    cam.lens = 50
    cam_obj = bpy.data.objects.new("Camera", cam)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0, -5, 1.5)
    cam_obj.rotation_euler = (math.radians(75), 0, 0)
    bpy.context.scene.camera = cam_obj
    return cam_obj

def add_text(brand, tagline, color):
    """Add brand name and tagline text"""
    # Brand name
    bpy.ops.object.text_add(location=(0, 0, -2.5))
    brand_obj = bpy.context.active_object
    brand_obj.data.body = brand
    brand_obj.data.align_x = 'CENTER'
    brand_obj.data.size = 0.8
    brand_obj.data.extrude = 0.02
    
    # Material for text
    text_mat = bpy.data.materials.new(name="TextMat")
    text_mat.use_nodes = True
    bsdf = text_mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.96, 0.96, 0.98, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.3
    bsdf.inputs['Metallic'].default_value = 0.1
    brand_obj.data.materials.append(text_mat)
    
    # Tagline
    bpy.ops.object.text_add(location=(0, 0, -3.2))
    tag_obj = bpy.context.active_object
    tag_obj.data.body = tagline
    tag_obj.data.align_x = 'CENTER'
    tag_obj.data.size = 0.22
    
    tag_mat = bpy.data.materials.new(name="TagMat")
    tag_mat.use_nodes = True
    tag_bsdf = tag_mat.node_tree.nodes['Principled BSDF']
    tag_bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    tag_bsdf.inputs['Roughness'].default_value = 0.4
    tag_obj.data.materials.append(tag_mat)

def hex_to_float(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def render_logo(brand, tagline, color1_hex, color2_hex, color3_hex, output_path):
    clear_scene()
    
    c1 = hex_to_float(color1_hex)
    c2 = hex_to_float(color2_hex)
    c3 = hex_to_float(color3_hex)
    
    # Create gem
    gem = create_gem_geometry()
    mat = create_glass_material(c1, c2, c3)
    gem.data.materials.append(mat)
    
    # Setup scene
    setup_lighting()
    setup_camera()
    add_text(brand, tagline, c2)
    
    # Render settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = output_path
    
    # Render
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED: {output_path}")

if __name__ == "__main__":
    # Parse args from command line
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    
    params = json.loads(argv[0]) if argv else {}
    
    brand = params.get('brand', 'Nexora')
    tagline = params.get('tagline', 'BUILDING A SMARTER TOMORROW')
    c1 = params.get('c1', '#0066FF')
    c2 = params.get('c2', '#7C3AED')
    c3 = params.get('c3', '#00CCFF')
    output = params.get('output', '/tmp/blender_logo.png')
    
    render_logo(brand, tagline, c1, c2, c3, output)
