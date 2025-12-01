import path from 'node:path';

import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv, type UserConfig } from 'vite';

const SRC_VERSION_DEFAULT = 'v1';

const topLevelModuleAliases = [
  'api',
  'components',
  'courses',
  'learning',
  'screens',
  'supervising',
  'teaching',
  'users',
];

const topLevelFileAliases = ['utils', 'mathjax_config', 'react_app'];

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const appVersion = env.APP_VERSION || SRC_VERSION_DEFAULT;
  const localBuild = env.LOCAL_BUILD === '1';
  const debug = env.DEBUG === '1';
  const buildDir = localBuild ? 'local' : 'prod';
  const target = process.env.BUILD_TARGET === 'css' ? 'css' : 'js';

  const srcRoot = path.resolve(__dirname, 'src', appVersion);
  const srcJsDir = path.resolve(srcRoot, 'js');
  const srcScssDir = path.resolve(srcRoot, 'scss');
  const nodeModulesDir = path.resolve(__dirname, 'node_modules');

  const aliases: Record<string, string> = {
    '~': srcRoot,
  };

  if (target === 'js') {
    aliases.jquery = path.resolve(nodeModulesDir, 'jquery');

    topLevelModuleAliases.forEach((name) => {
      aliases[name] = path.resolve(srcJsDir, name);
    });

    topLevelFileAliases.forEach((name) => {
      aliases[name] = path.resolve(srcJsDir, name);
    });
  } else {
    aliases.components = path.resolve(srcScssDir, "components");
  }

  const shared: Pick<UserConfig, "appType" | "resolve" | "define" | "css"> = {
    appType: "custom",
    resolve: {
      alias: aliases,
    },
    define: {
      "process.env.NODE_ENV": JSON.stringify(
        mode === "development" ? "development" : "production",
      ),
    },
    css: {
      preprocessorOptions: {
        scss: {
          includePaths: [nodeModulesDir, srcScssDir],
        },
        sass: {
          includePaths: [nodeModulesDir, srcScssDir],
        },
      },
    },
  };

  if (target === "css") {
    const cssConfig: UserConfig = {
      ...shared,
      base: `/static/${appVersion}/dist/css/`,
      build: {
        target: "es2020",
        sourcemap: localBuild,
        outDir: path.resolve(__dirname, "assets", appVersion, "dist", "css"),
        emptyOutDir: true,
        manifest: true,
        minify: debug ? false : "esbuild",
        rollupOptions: {
          input: {
            center_staff: path.resolve(srcScssDir, "center/staff.scss"),
            center_style: path.resolve(srcScssDir, "center/style.scss"),
          },
          output: {
            entryFileNames: `[name].js`,
            assetFileNames(assetInfo) {
              const ext = path.extname(assetInfo.name || "");

              if (ext === ".css") {
                return `[name].css`;
              }

              if ((assetInfo.name || "").includes("node_modules/")) {
                const normalizedPath = (assetInfo.name || "").replace(
                  /\\/g,
                  "/",
                );
                const [, nodeModulesRelative] =
                  normalizedPath.split("node_modules/");
                const dir = path.dirname(nodeModulesRelative);
                return `assets/${dir}/[hash][extname]`;
              }

              return `assets/[name]-[hash][extname]`;
            },
          },
        },
      },
    };

    return cssConfig;
  }

  const jsConfig: UserConfig = {
    ...shared,
    base: `/static/${appVersion}/dist/${buildDir}/`,
    plugins: [react()],
    build: {
      target: "es2020",
      sourcemap: localBuild,
      outDir: path.resolve(__dirname, "assets", appVersion, "dist", buildDir),
      emptyOutDir: true,
      manifest: true,
      minify: debug ? false : "esbuild",
      modulePreload: false,
      rollupOptions: {
        input: {
          app: path.resolve(srcJsDir, "app.js"),
        },
        output: {
          format: "iife",
          manualChunks: undefined,
          inlineDynamicImports: true,
          entryFileNames: `[name]-[hash].js`,
          chunkFileNames: `[name]-[hash].js`,
          assetFileNames(assetInfo) {
            const normalizedPath = (assetInfo.name || "").replace(/\\/g, "/");

            if (normalizedPath.includes("node_modules/")) {
              const [, nodeModulesRelative] =
                normalizedPath.split("node_modules/");
              const dir = path.dirname(nodeModulesRelative);
              return `assets/${dir}/[hash][extname]`;
            }

            return `assets/[name]-[hash][extname]`;
          },
        },
      },
    },
  };

  return jsConfig;
});
