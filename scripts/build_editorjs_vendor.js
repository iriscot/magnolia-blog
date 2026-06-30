#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const optional = process.argv.includes('--optional');
const projectRoot = path.resolve(__dirname, '..');
const nodeModulesDir = path.join(projectRoot, 'node_modules');
const vendorRoot = path.join(projectRoot, 'static', 'vendor');

const packages = [
  {
    name: '@editorjs/editorjs',
    target: '@editorjs/editorjs/dist/editor.js',
    candidates: [
      'dist/editorjs.umd.js',
      'dist/editorjs.umd.min.js',
      'dist/editor.js',
      'dist/editorjs.js',
    ],
  },
  {
    name: '@editorjs/header',
    target: '@editorjs/header/dist/bundle.js',
    candidates: ['dist/bundle.js'],
  },
  {
    name: '@editorjs/image',
    target: '@editorjs/image/dist/bundle.js',
    candidates: ['dist/bundle.js'],
  },
  {
    name: '@editorjs/quote',
    target: '@editorjs/quote/dist/bundle.js',
    candidates: ['dist/bundle.js'],
  },
  {
    name: '@editorjs/list',
    target: '@editorjs/list/dist/bundle.js',
    candidates: [
      'dist/editorjs-list.umd.js',
      'dist/editorjs-list.umd.min.js',
      'dist/bundle.js',
    ],
  },
  {
    name: '@editorjs/embed',
    target: '@editorjs/embed/dist/bundle.js',
    candidates: ['dist/bundle.js'],
  },
  {
    name: '@editorjs/raw',
    target: '@editorjs/raw/dist/bundle.js',
    candidates: ['dist/bundle.js'],
  },
  {
    name: '@editorjs/delimiter',
    target: '@editorjs/delimiter/dist/bundle.js',
    candidates: ['dist/bundle.js'],
  },
];

const staleVendorDirs = [
  '@editorjs/checklist',
];

function fileExists(filePath) {
  try {
    return fs.statSync(filePath).isFile();
  } catch (_error) {
    return false;
  }
}

function readPackageJson(packageDir) {
  const packageJsonPath = path.join(packageDir, 'package.json');

  if (!fileExists(packageJsonPath)) {
    return {};
  }

  try {
    return JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  } catch (_error) {
    return {};
  }
}

function packageSlug(packageName) {
  return packageName.split('/').pop().replace(/^editorjs-/, '');
}

function fieldCandidates(packageJson) {
  const fields = ['browser', 'unpkg', 'jsdelivr', 'main'];
  const values = [];

  for (const field of fields) {
    const value = packageJson[field];
    if (typeof value === 'string' && value.endsWith('.js')) {
      values.push(value.replace(/^\.\//, ''));
    }
  }

  if (packageJson.exports && packageJson.exports['.']) {
    const rootExport = packageJson.exports['.'];
    for (const key of ['browser', 'default', 'require', 'import']) {
      const value = rootExport[key];
      if (typeof value === 'string' && value.endsWith('.js') && !value.endsWith('.mjs')) {
        values.push(value.replace(/^\.\//, ''));
      }
    }
  }

  return values;
}

function discoverDistCandidates(packageDir) {
  const distDir = path.join(packageDir, 'dist');

  if (!fs.existsSync(distDir)) {
    return [];
  }

  const files = fs
    .readdirSync(distDir)
    .filter((file) => file.endsWith('.js') && !file.endsWith('.mjs'));

  const score = (file) => {
    if (/\.umd\.js$/.test(file)) return 0;
    if (/\.umd\.min\.js$/.test(file)) return 1;
    if (file === 'bundle.js') return 2;
    if (/browser|standalone/i.test(file)) return 3;
    if (/index|main/i.test(file)) return 4;
    return 10;
  };

  return files
    .sort((a, b) => score(a) - score(b) || a.localeCompare(b))
    .map((file) => path.join('dist', file));
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function resolvePackageSource(pkg) {
  const packageDir = path.join(nodeModulesDir, pkg.name);

  if (!fs.existsSync(packageDir)) {
    throw new Error(`Missing package ${pkg.name} in node_modules. Run npm install first.`);
  }

  const packageJson = readPackageJson(packageDir);
  const slug = packageSlug(pkg.name);
  const candidates = unique([
    ...pkg.candidates,
    ...fieldCandidates(packageJson),
    `dist/${slug}.umd.js`,
    `dist/${slug}.umd.min.js`,
    `dist/${slug}.js`,
    `dist/index.umd.js`,
    `dist/index.js`,
    ...discoverDistCandidates(packageDir),
  ]);

  for (const candidate of candidates) {
    const source = path.join(packageDir, candidate);

    if (fileExists(source)) {
      return { source, candidate };
    }
  }

  throw new Error(
    `Could not find a browser bundle for ${pkg.name}. Checked: ${candidates.join(', ')}`
  );
}

function copyPackage(pkg) {
  const { source, candidate } = resolvePackageSource(pkg);
  const target = path.join(vendorRoot, pkg.target);

  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(source, target);

  console.log(
    `Copied ${pkg.name}/${candidate} -> ${path.relative(projectRoot, target)}`
  );
}

function removeStaleVendorDirs() {
  for (const staleDir of staleVendorDirs) {
    const fullPath = path.join(vendorRoot, staleDir);
    fs.rmSync(fullPath, { recursive: true, force: true });
  }
}

function fail(error) {
  const message = `\nFailed to build EditorJS vendor files: ${error.message}`;

  if (optional) {
    console.warn(`${message}\nContinuing because this was called from npm postinstall.`);
    process.exit(0);
  }

  console.error(message);
  process.exit(1);
}

try {
  if (!fs.existsSync(nodeModulesDir)) {
    throw new Error('node_modules not found. Run npm install first.');
  }

  removeStaleVendorDirs();

  for (const pkg of packages) {
    copyPackage(pkg);
  }

  console.log('\nEditorJS vendor files are ready in static/vendor/.');
} catch (error) {
  fail(error);
}
