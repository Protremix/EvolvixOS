#!/usr/bin/env python3
"""
Comprehensive polish fix for EvolvixOS landing + platform.
Fix all remaining 'app builder' references, Base44 mentions, and engineering positioning.
"""

def patch_file(filepath, replacements):
    with open(filepath, "r") as f:
        content = f.read()
    for old, new in replacements:
        count = content.count(old)
        content = content.replace(old, new)
        if count > 0:
            print(f"  {count}x: {old[:60]}...")
    with open(filepath, "w") as f:
        f.write(content)

# ═══ LANDING.HTML FIXES ═══
landing_fixes = [
    # 1. Feature card title
    ("No-Code App Builder", "Engineering Workbench"),
    
    # 2. Feature card badge
    ('Base44-style', 'Self-Hosted'),
    
    # 3. Feature card description
    ("Build full-stack applications with a drag-and-drop page builder, entity-based CRUD APIs, and auto-generated SDKs. No code required — just describe what you want.",
     "Engineer full-stack systems with a drag-and-drop page builder, entity-based CRUD APIs, and auto-generated SDKs. Just describe what you want."),
    
    # 4. Voice card — app building
    ("Control media generation, server management, and app building through natural language voice commands.",
     "Control media generation, server management, and system engineering through natural language voice commands."),
    
    # 5. Architecture section — Base44 reference
    ("EvolvixOS architecture mirrors Base44's proven design — entity-based data, auto-generated APIs,\n      and an AI-driven builder layer, all on your own infrastructure.",
     "EvolvixOS is built on a proven layered architecture — entity-based data, auto-generated APIs,\n      and an AI-driven engineering layer, all on your own infrastructure."),
    
    # 6. Architecture layer title
    ("Builder Layer — AI-Powered No-Code", "Workbench Layer — AI-Powered Engineering"),
    
    # 7. Architecture layer description
    ("Describe your app in natural language. The AI builder creates entities, pages, and functions automatically.",
     "Describe your system in natural language. The Workbench creates schemas, pages, and functions automatically."),
    
    # 8. Developer Experience
    ("Everything you need to build and ship AI-powered applications without fighting infrastructure.",
     "Everything you need to engineer and ship AI-powered systems without fighting infrastructure."),
    
    # 9. Public app viewer
    ("Public app viewer — share your apps with anyone via URL",
     "Public service viewer — share your services with anyone via URL"),
    
    # 10-16. Pricing fixes
    ("Perfect for exploring the platform and building your first AI apps.",
     "Perfect for exploring the platform and engineering your first AI systems."),
    ("3 Entities / Apps", "3 Entities / Services"),
    ("5 Pages per App", "5 Pages per Service"),
    ("Page Builder + App Viewer", "Page Builder + Service Viewer"),
    ("For developers building production AI apps with cloud model access.",
     "For developers engineering production AI systems with cloud model access."),
    ("Unlimited Entities / Apps", "Unlimited Entities / Services"),
    ("Unlimited Pages per App", "Unlimited Pages per Service"),
    
    # 17. CTA
    ("Ready to Build Something", "Ready to Engineer Something"),
    
    # 18. Hero subtitle — double "full-stack"
    ("281+ AI models, full-stack media production, and zero-knowledge dashboards",
     "281+ AI models, cinematic media production, and zero-knowledge dashboards"),
    
    # 19. Footer — Studio → Workbench for consistency
    # Keep Studio as it's the product name for the dashboard
    
    # 20. "build and ship" in other places
    ("build and ship AI-powered applications", "engineer and ship AI-powered systems"),
]

print("═══ PATCHING LANDING.HTML ═══")
patch_file("/opt/evolvixos/web/landing.html", landing_fixes)

print("\n═══ PATCHING LANDING_NEW.HTML ═══")
patch_file("/opt/evolvixos/web/landing_new.html", landing_fixes)

print("\n═══ PATCHING INDEX_NEW.HTML ═══")
patch_file("/opt/evolvixos/web/index_new.html", landing_fixes)

# ═══ PLATFORM.HTML FIXES ═══
platform_fixes = [
    # Any remaining "app" references in visible text
    ("' app called '", "' service called '"),
    ("Creating app from template", "Creating service from template"),
    
    # "Build: App" in any remaining JS
    ("'Build: App'", "'Build: Service'"),
]

print("\n═══ PATCHING PLATFORM.HTML ═══")
patch_file("/opt/evolvixos/web/platform.html", platform_fixes)

# ═══ VERIFY ═══
print("\n═══ VERIFICATION ═══")
import subprocess
for f in ["landing.html", "platform.html"]:
    result = subprocess.run(
        ["grep", "-cin", "app builder\|no-code\|Base44\|AI Builder\|No-Code"],
        capture_output=True, text=True
    )
    # More specific check
    result = subprocess.run(
        ["grep", "-in", "\\bapp builder\\b\\|\\bno-code\\b\\|Base44-style\\|No-Code App",
         f"/opt/evolvixos/web/{f}"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        print(f"  ⚠ {f}: {result.stdout.strip()}")
    else:
        print(f"  ✓ {f}: clean")

print("\n✅ Polish complete!")
