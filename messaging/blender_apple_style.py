#!/usr/bin/env python3
"""
Blender Logo — Apple/Google Style
Key principles:
- Clean, bright, diffused lighting (product photography style)
- Simple perfect geometry with smooth bevels
- Subtle gradient glass (not overly complex shader)
- High samples (512) for noise-free, flawless rendering
- Crisp typography
- Minimal scene — no extra objects
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

def create_clean_hexagon():
    """Simple, perfect hexagonal prism with smooth bevels"""
    mesh = bpy.data.meshes.new("HexIcon")
    obj = bpy.data.objects.new("HexIcon", mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    n = 6
    r = 1.5
    depth = 0.4
    
    top = []
    bot = []
    for i in range(n):
        angle = (2 * math.pi * i) / n + math.pi/2
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        top.append(bm.verts.new((x, y, depth/2)))
        bot.append(bm.verts.new((x, y, -depth/2)))
    
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([bot[i], top[i], top[j], bot[j]])
    
    bm.to_mesh(mesh)
    bm.free()
    
    # Smooth bevel — this is what gives the Apple-like edge quality
    bpy.context.view_layer.objects.active = obj
    bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.12
    bevel.segments = 8
    bevel.profile = 0.7  # rounded profile for smoother edges
    bpy.ops.object.modifier_apply(modifier="Bevel")
    
    # Smooth shading
    for poly in obj.data.polygons:
        poly.use_smooth = True
    
    return obj

def create_apple_glass_material(c1, c2, c3):
    """Clean, subtle glass — not overly complex"""
    mat = bpy.data.materials.new(name="AppleGlass")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)
    
    # Principled BSDF — use this as base for cleaner look
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (400, 0)
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['IOR'].default_value = 1.45
    bsdf.inputs['Transmission Weight'].default_value = 0.9  # Glass transmission
    bsdf.inputs['Coat Weight'].default_value = 1.0  # Clear coat for glossy surface
    bsdf.inputs['Coat Roughness'].default_value = 0.02
    
    # Gradient color ramp for the tint
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = (100, 100)
    ramp.color_ramp.interpolation = 'EASE'
    ramp.color_ramp.elements[0].color = (c1[0], c1[1], c1[2], 1.0)
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[1].color = (c3[0], c3[1], c3[2], 1.0)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements.new(0.5)
    ramp.color_ramp.elements[1].color = (c2[0], c2[1], c2[2], 1.0)
    
    # Texture coordinate
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-200, 100)
    mapping = nodes.new('ShaderNodeMapping')
    mapping.location = (0, 100)
    
    # Fresnel for edge highlight
    fresnel = nodes.new('ShaderNodeFresnel')
    fresnel.location = (200, -200)
    fresnel.inputs['IOR'].default_value = 1.45
    
    # Color mix for fresnel edge
    edge_mix = nodes.new('ShaderNodeMixRGB')
    edge_mix.location = (400, -200)
    edge_mix.inputs['Color1'].default_value = (c2[0], c2[1], c2[2], 1.0)
    edge_mix.inputs['Color2'].default_value = (1.0, 1.0, 1.0, 1.0)
    
    links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(fresnel.outputs['Fac'], edge_mix.inputs['Fac'])
    links.new(edge_mix.outputs['Color'], bsdf.inputs['Coat Tint'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def setup_apple_lighting(c1, c2, c3):
    """Soft, diffused, bright lighting — Apple product photography style"""
    # Main key — large, soft, bright
    key = bpy.data.lights.new(name="Key", type='AREA')
    key.energy = 3000
    key.size = 8
    key.color = (1.0, 0.98, 0.95)
    key_obj = bpy.data.objects.new("Key", key)
    bpy.context.collection.objects.link(key_obj)
    key_obj.location = (3, -8, 10)
    key_obj.rotation_euler = (math.radians(15), math.radians(10), math.radians(20))
    
    # Fill — very large, very soft
    fill = bpy.data.lights.new(name="Fill", type='AREA')
    fill.energy = 1000
    fill.size = 12
    fill.color = (0.85, 0.9, 1.0)
    fill_obj = bpy.data.objects.new("Fill", fill)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.location = (-8, -6, 8)
    fill_obj.rotation_euler = (math.radians(20), math.radians(-15), math.radians(-25))
    
    # Rim — subtle, brand-colored
    rim = bpy.data.lights.new(name="Rim", type='AREA')
    rim.energy = 1500
    rim.size = 5
    rim.color = (c2[0], c2[1], c2[2])
    rim_obj = bpy.data.objects.new("Rim", rim)
    bpy.context.collection.objects.link(rim_obj)
    rim_obj.location = (-2, 8, 6)
    rim_obj.rotation_euler = (math.radians(-10), math.radians(5), math.radians(175))
    
    # Top light — soft, overhead
    top = bpy.data.lights.new(name="Top", type='AREA')
    top.energy = 800
    top.size = 6
    top.color = (1.0, 1.0, 1.0)
    top_obj = bpy.data.objects.new("Top", top)
    bpy.context.collection.objects.link(top_obj)
    top_obj.location = (0, -2, 12)
    top_obj.rotation_euler = (math.radians(0), 0, 0)
    
    # World — dark but not pitch black, subtle gradient
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()
    
    woutput = wnodes.new('ShaderNodeOutputWorld')
    woutput.location = (400, 0)
    
    wgrad = wnodes.new('ShaderNodeTexGradient')
    wgrad.location = (-200, 0)
    
    wcoord = wnodes.new('ShaderNodeTexCoord')
    wcoord.location = (-400, 0)
    
    wcramp = wnodes.new('ShaderNodeValToRGB')
    wcramp.location = (0, 0)
    wcramp.color_ramp.elements[0].color = (0.06, 0.05, 0.1, 1.0)
    wcramp.color_ramp.elements[1].color = (0.01, 0.01, 0.03, 1.0)
    
    wbg = wnodes.new('ShaderNodeBackground')
    wbg.location = (200, 0)
    wbg.inputs['Strength'].default_value = 2.0
    
    wlinks.new(wcoord.outputs['Generated'], wgrad.inputs['Vector'])
    wlinks.new(wgrad.outputs['Color'], wcramp.inputs['Fac'])
    wlinks.new(wcramp.outputs['Color'], wbg.inputs['Color'])
    wlinks.new(wbg.outputs['Background'], woutput.inputs['Surface'])

def setup_camera():
    cam = bpy.data.cameras.new(name="Cam")
    cam.lens = 85  # longer lens for less distortion
    cam_obj = bpy.data.objects.new("Camera", cam)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0, -7, 0.3)
    cam_obj.rotation_euler = (math.radians(88), 0, 0)
    bpy.context.scene.camera = cam_obj

def add_text(brand, tagline, c2):
    # Brand name
    bpy.ops.object.text_add(location=(0, 0, -2.6))
    brand_obj = bpy.context.active_object
    brand_obj.data.body = brand
    brand_obj.data.align_x = 'CENTER'
    brand_obj.data.size = 0.8
    brand_obj.data.extrude = 0.02
    brand_obj.data.bevel_depth = 0.006
    brand_obj.data.bevel_resolution = 4
    
    font_path = "/opt/evolvixos/fonts/Poppins-ExtraBold.ttf"
    if os.path.exists(font_path):
        brand_obj.data.font = bpy.data.fonts.load(font_path)
    
    text_mat = bpy.data.materials.new(name="TextMat")
    text_mat.use_nodes = True
    bsdf = text_mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (0.97, 0.97, 0.99, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['Metallic'].default_value = 0.3
    brand_obj.data.materials.append(text_mat)
    
    # Tagline
    bpy.ops.object.text_add(location=(0, 0, -3.4))
    tag_obj = bpy.context.active_object
    tag_obj.data.body = tagline
    tag_obj.data.align_x = 'CENTER'
    tag_obj.data.size = 0.14
    
    tag_font = "/opt/evolvixos/fonts/Poppins-Medium.ttf"
    if os.path.exists(tag_font):
        tag_obj.data.font = bpy.data.fonts.load(tag_font)
    
    tag_mat = bpy.data.materials.new(name="TagMat")
    tag_mat.use_nodes = True
    tag_bsdf = tag_mat.node_tree.nodes['Principled BSDF']
    tag_bsdf.inputs['Base Color'].default_value = (c2[0], c2[1], c2[2], 1.0)
    tag_bsdf.inputs['Roughness'].default_value = 0.25
    tag_bsdf.inputs['Emission Color'].default_value = (c2[0], c2[1], c2[2], 1.0)
    tag_bsdf.inputs['Emission Strength'].default_value = 3.0
    tag_obj.data.materials.append(tag_mat)

def render_apple_style(brand, tagline, c1_hex, c2_hex, c3_hex, output_path):
    clear_scene()
    c1 = hex_to_float(c1_hex)
    c2 = hex_to_float(c2_hex)
    c3 = hex_to_float(c3_hex)
    
    icon = create_clean_hexagon()
    mat = create_apple_glass_material(c1, c2, c3)
    icon.data.materials.append(mat)
    
    setup_apple_lighting(c1, c2, c3)
    setup_camera()
    add_text(brand, tagline, c2)
    
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 512
    scene.cycles.use_denoising = True
    # scene.cycles.denoising_quality = 'HIGH'
    scene.render.resolution_x = 2000
    scene.render.resolution_y = 2400
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
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
    render_apple_style(
        params.get('brand', 'NEXORA'),
        params.get('tagline', 'BUILDING A SMARTER TOMORROW'),
        params.get('c1', '#0066FF'),
        params.get('c2', '#7C3AED'),
        params.get('c3', '#00CCFF'),
        params.get('output', '/tmp/apple_logo.png')
    )
