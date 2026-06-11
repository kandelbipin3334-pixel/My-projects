import os
import time
import threading
import http.server
import socketserver
import webbrowser

# --- 1. DEEP-SPACE MILKY WAY WITH BACKGROUND STARFIELD ---
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Milky Way Simulation with Starfield</title>
    <style>
        body { margin: 0; overflow: hidden; background-color: #000002; }
        canvas { display: block; width: 100vw; height: 100vh; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <script>
        // Physical parameters for the galaxy and background
        const parameters = {
            count: 140000,          // Galaxy stars
            bgCount: 30000,         // Distant background stars
            size: 0.006,            // Sharp, crisp stars
            bgSize: 0.003,          // Fainter background star size
            radius: 7,              
            branches: 4,            
            spin: 0.85,             
            randomness: 0.42,       
            power: 4.0,             
            barLength: 1.6,         
            
            coreColor: '#fff2d5',    
            midColor: '#e085ff',     
            edgeColor: '#091e52'     
        };

        let scene, camera, renderer, geometry, material, points, controls;
        let bgGeometry, bgMaterial, bgPoints;

        function init() {
            scene = new THREE.Scene();
            
            // Subtle deep cosmic fog
            scene.fog = new THREE.FogExp2('#000002', 0.04);

            camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 150);
            camera.position.set(0, 7, 9);

            renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            document.body.appendChild(renderer.domElement);

            // Controls for zooming/rotating
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.minDistance = 1.2;
            controls.maxDistance = 45; // Allowed further zoom out to see background stars

            // Generates both systems
            generateMilkyWay();
            generateBackgroundStars();

            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });

            animate();
        }

        // Texture generator for soft stars
        const createStarMap = (glowIntensity = 1) => {
            const canvas = document.createElement('canvas');
            canvas.width = 16;
            canvas.height = 16;
            const ctx = canvas.getContext('2d');
            const gradient = ctx.createRadialGradient(8, 8, 0, 8, 8, 8);
            gradient.addColorStop(0, `rgba(255,255,255,${glowIntensity})`);
            gradient.addColorStop(0.2, `rgba(240,245,255,${glowIntensity * 0.6})`);
            gradient.addColorStop(1, 'rgba(0,0,0,0)');
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, 16, 16);
            return new THREE.CanvasTexture(canvas);
        };

        // 1. ADDED: DISTANT BACKGROUND STARFIELD
        function generateBackgroundStars() {
            bgGeometry = new THREE.BufferGeometry();
            const positions = new Float32Array(parameters.bgCount * 3);
            const colors = new Float32Array(parameters.bgCount * 3);

            for(let i = 0; i < parameters.bgCount; i++) {
                const i3 = i * 3;

                // Scatter background stars uniformly in a massive sphere around the galaxy
                const u = Math.random();
                const v = Math.random();
                const theta = u * 2.0 * Math.PI;
                const phi = Math.acos(2.0 * v - 1.0);
                
                // Keep background stars far away (between distance 30 and 80)
                const distance = 30 + Math.random() * 50;

                positions[i3]     = distance * Math.sin(phi) * Math.cos(theta);
                positions[i3 + 1] = distance * Math.sin(phi) * Math.sin(theta);
                positions[i3 + 2] = distance * Math.cos(phi);

                // Varied stellar temperatures (mostly white, blue-white, and dim orange)
                const type = Math.random();
                if (type > 0.8) {
                    colors[i3] = 0.7; colors[i3+1] = 0.8; colors[i3+2] = 1.0; // Bluish
                } else if (type > 0.65) {
                    colors[i3] = 1.0; colors[i3+1] = 0.8; colors[i3+2] = 0.6; // Orange-ish
                } else {
                    const brightness = 0.5 + Math.random() * 0.5;
                    colors[i3] = brightness; colors[i3+1] = brightness; colors[i3+2] = brightness; // White/Grey
                }
            }

            bgGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            bgGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            bgMaterial = new THREE.PointsMaterial({
                size: parameters.bgSize,
                sizeAttenuation: true,
                depthWrite: false,
                vertexColors: true,
                map: createStarMap(0.8),
                transparent: true
            });

            bgPoints = new THREE.Points(bgGeometry, bgMaterial);
            scene.add(bgPoints);
        }

        // 2. UPGRADED: CORE GALAXY SYSTEM
        function generateMilkyWay() {
            if(points !== undefined && points !== null){
                geometry.dispose();
                material.dispose();
                scene.remove(points);
            }

            material = new THREE.PointsMaterial({
                size: parameters.size,
                sizeAttenuation: true,
                depthWrite: false,
                blending: THREE.AdditiveBlending,
                vertexColors: true,
                map: createStarMap(1),
                transparent: true
            });

            geometry = new THREE.BufferGeometry();
            const positions = new Float32Array(parameters.count * 3);
            const colors = new Float32Array(parameters.count * 3);

            const cCore = new THREE.Color(parameters.coreColor);
            const cMid = new THREE.Color(parameters.midColor);
            const cEdge = new THREE.Color(parameters.edgeColor);

            for(let i = 0; i < parameters.count; i++) {
                const i3 = i * 3;
                const radius = Math.pow(Math.random(), 1.6) * parameters.radius;
                
                let x = 0, y = 0, z = 0;

                if (radius < parameters.barLength) {
                    const progress = radius / parameters.barLength;
                    x = (Math.random() - 0.5) * parameters.barLength * 2;
                    y = (Math.random() - 0.5) * 0.28 * (1.0 - progress);
                    z = (Math.random() - 0.5) * 0.38;
                    
                    const barAngle = 0.45;
                    const rx = x * Math.cos(barAngle) - z * Math.sin(barAngle);
                    const rz = x * Math.sin(barAngle) + z * Math.cos(barAngle);
                    x = rx; z = rz;
                } else {
                    const spinAngle = (radius - parameters.barLength) * parameters.spin;
                    const branchAngle = ((i % parameters.branches) / parameters.branches) * Math.PI * 2;

                    const randomX = Math.pow(Math.random(), parameters.power) * (Math.random() < 0.5 ? 1 : -1) * parameters.randomness * radius;
                    const randomY = Math.pow(Math.random(), parameters.power) * (Math.random() < 0.5 ? 1 : -1) * (parameters.randomness * 0.35) * radius;
                    const randomZ = Math.pow(Math.random(), parameters.power) * (Math.random() < 0.5 ? 1 : -1) * parameters.randomness * radius;

                    x = Math.cos(branchAngle + spinAngle) * radius + randomX;
                    y = randomY;
                    z = Math.sin(branchAngle + spinAngle) * radius + randomZ;
                }

                positions[i3]     = x;
                positions[i3 + 1] = y;
                positions[i3 + 2] = z;

                let mixedColor = cCore.clone();
                if (radius < parameters.radius * 0.25) {
                    const alpha = radius / (parameters.radius * 0.25);
                    mixedColor.lerp(cMid, alpha);
                } else {
                    const alpha = (radius - parameters.radius * 0.25) / (parameters.radius * 0.75);
                    mixedColor.lerp(cEdge, alpha);
                }
                
                // Realistic natural noise variance for nebulae clouds
                mixedColor.r += (Math.random() - 0.5) * 0.06;
                mixedColor.g += (Math.random() - 0.5) * 0.04;
                mixedColor.b += (Math.random() - 0.5) * 0.08;

                colors[i3]     = mixedColor.r;
                colors[i3 + 1] = mixedColor.g;
                colors[i3 + 2] = mixedColor.b;
            }

            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            points = new THREE.Points(geometry, material);
            scene.add(points);
        }

        function animate() {
            requestAnimationFrame(animate);
            controls.update(); 

            if (points) {
                points.rotation.y += 0.0006; // Core galaxy rotation speed
            }
            if (bgPoints) {
                bgPoints.rotation.y += 0.0001; // Background stars move much slower to create parallax depth
            }
            
            renderer.render(scene, camera);
        }

        window.onload = init;
    </script>
</body>
</html>
"""

# Store configuration code to runtime directory
with open("index.html", "w") as f:
    f.write(html_content)

# --- 2. BACKEND LOCAL SERVER ---
PORT = 8555
class QuietServer(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), QuietServer) as httpd:
        httpd.serve_forever()

server_worker = threading.Thread(target=start_server, daemon=True)
server_worker.start()

# --- 3. AUTO LAUNCH ---
print("Rendering astronomical particle assets...")
time.sleep(1.2)

print("Opening Upgraded Milky Way with Starfield...")
url = f"http://127.0.0.1:{PORT}/index.html"
webbrowser.open(url)

while True:
    time.sleep(1)
