import { useReducedMotion } from '../utils/motion-preference';
import { useEffect, useRef } from 'react';
import { useInView } from 'motion/react';
import {
  ACESFilmicToneMapping,
  AmbientLight,
  Color,
  DirectionalLight,
  Mesh,
  MeshPhysicalMaterial,
  PerspectiveCamera,
  PMREMGenerator,
  Scene,
  TorusKnotGeometry,
  WebGLRenderer,
} from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { site } from '../data/site';

export function VoiceSculpture({ paused = false }: { paused?: boolean }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const visible = useInView(ref);
  const reduced = useReducedMotion();
  const running = useRef(false);
  useEffect(() => {
    running.current = visible && !paused && !reduced;
  }, [visible, paused, reduced]);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const cleanup: Array<() => void> = [];
    const dispose = () => {
      for (const release of cleanup.reverse()) release();
      cleanup.length = 0;
    };
    try {
      const renderer = new WebGLRenderer({
        canvas,
        alpha: true,
        antialias: true,
        powerPreference: 'low-power',
      });
      cleanup.push(() => renderer.dispose());
      const config = site.visual;
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, config.maxPixelRatio));
      renderer.toneMapping = ACESFilmicToneMapping;
      renderer.toneMappingExposure = config.exposure;
      const scene = new Scene();
      const camera = new PerspectiveCamera(
        config.cameraFov,
        1,
        config.cameraNear,
        config.cameraFar,
      );
      camera.position.z = config.cameraDistance;
      const environment = new RoomEnvironment();
      cleanup.push(() => environment.dispose());
      const generator = new PMREMGenerator(renderer);
      cleanup.push(() => generator.dispose());
      const target = generator.fromScene(environment);
      cleanup.push(() => target.dispose());
      scene.environment = target.texture;
      const geometry = new TorusKnotGeometry(
        config.torusRadius,
        config.tubeRadius,
        config.tubularSegments,
        config.radialSegments,
        config.knotP,
        config.knotQ,
      );
      cleanup.push(() => geometry.dispose());
      const material = new MeshPhysicalMaterial({
        color: new Color(config.colors[0]),
        metalness: config.metalness,
        roughness: config.roughness,
        clearcoat: config.clearcoat,
        clearcoatRoughness: config.clearcoatRoughness,
        iridescence: config.iridescence,
        iridescenceIOR: config.iridescenceIOR,
        envMapIntensity: config.environmentIntensity,
      });
      cleanup.push(() => material.dispose());
      const sculpture = new Mesh(geometry, material);
      sculpture.rotation.set(...config.initialRotation);
      scene.add(sculpture);
      scene.add(new AmbientLight(config.colors[0], config.ambientIntensity));
      for (const [index, color] of config.colors.entries()) {
        const light = new DirectionalLight(color, config.lightIntensity);
        const angle = (index * Math.PI * 2) / config.colors.length;
        light.position.set(
          Math.cos(angle) * camera.position.z,
          Math.sin(angle) * camera.position.z,
          camera.position.z,
        );
        scene.add(light);
      }
      let frame = 0,
        last = 0,
        angle = 0;
      let pointerX = 0,
        pointerY = 0;
      const resize = () => {
        const box = canvas.getBoundingClientRect();
        if (!box.width || !box.height) return;
        renderer.setSize(box.width, box.height, false);
        camera.aspect = box.width / box.height;
        camera.updateProjectionMatrix();
        renderer.render(scene, camera);
      };
      const observer = new ResizeObserver(resize);
      cleanup.push(() => observer.disconnect());
      observer.observe(canvas);
      const move = (event: PointerEvent) => {
        const box = canvas.getBoundingClientRect();
        pointerX = ((event.clientX - box.left) / box.width - 0.5) * config.pointerTilt;
        pointerY = ((event.clientY - box.top) / box.height - 0.5) * config.pointerTilt;
      };
      const leave = () => {
        pointerX = 0;
        pointerY = 0;
      };
      canvas.addEventListener('pointermove', move);
      canvas.addEventListener('pointerleave', leave);
      cleanup.push(() => {
        canvas.removeEventListener('pointermove', move);
        canvas.removeEventListener('pointerleave', leave);
      });
      let lost = false;
      const contextLost = (event: Event) => {
        event.preventDefault();
        lost = true;
        canvas.dataset.renderer = 'fallback';
      };
      const contextRestored = () => {
        lost = false;
        canvas.dataset.renderer = 'webgl';
        resize();
      };
      canvas.addEventListener('webglcontextlost', contextLost);
      canvas.addEventListener('webglcontextrestored', contextRestored);
      cleanup.push(() => {
        canvas.removeEventListener('webglcontextlost', contextLost);
        canvas.removeEventListener('webglcontextrestored', contextRestored);
      });
      const draw = (time: number) => {
        if (!lost && running.current && document.visibilityState === 'visible') {
          const delta = last ? Math.min(time - last, config.maxFrameDeltaMs) : 0;
          angle += delta * config.rotationSpeed;
          sculpture.rotation.y = config.initialRotation[1] + angle + pointerX;
          sculpture.rotation.x = config.initialRotation[0] + pointerY;
          renderer.render(scene, camera);
          canvas.dataset.frames = String(Number(canvas.dataset.frames ?? 0) + 1);
        }
        last = time;
        frame = requestAnimationFrame(draw);
      };
      canvas.dataset.renderer = 'webgl';
      resize();
      frame = requestAnimationFrame(draw);
      cleanup.push(() => cancelAnimationFrame(frame));
      return dispose;
    } catch {
      dispose();
      canvas.dataset.renderer = 'fallback';
      return;
    }
  }, []);
  return (
    <div className="voice-sculpture" aria-hidden="true">
      <div className="sculpture-fallback">
        <i />
        <i />
        <i />
      </div>
      <canvas ref={ref} />
    </div>
  );
}
