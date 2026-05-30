#!/usr/bin/env node
/*
 * SAP Datasphere MCP Server — Node bootstrap.
 *
 * This shim is what `npx @rahulsethi/sap-datasphere-mcp` runs.
 *
 * Goal: hand off cleanly to the real Python entrypoint without making the
 * user install Python tooling first. We try three Python launchers in
 * preference order and forward stdio so the MCP host on the other end
 * doesn't even know there was a Node layer in the middle.
 *
 * Preference order:
 *   1. `uvx sap-datasphere-mcp`           (uv — fastest, no global install)
 *   2. `pipx run sap-datasphere-mcp`      (pipx)
 *   3. `python -m sap_datasphere_mcp`     (already on PATH)
 *
 * If none of these are available we print a clear, actionable message and
 * exit non-zero — never silently fall through.
 */

'use strict';

const { spawn } = require('node:child_process');
const { existsSync } = require('node:fs');
const path = require('node:path');

const PACKAGE_NAME = 'sap-datasphere-mcp';
const VERSION = '1.0.0';

const args = process.argv.slice(2);
if (args.length === 1 && (args[0] === '--node-wrapper-version' || args[0] === '--wrapper-version')) {
  console.log(`@rahulsethi/sap-datasphere-mcp (Node wrapper) ${VERSION}`);
  process.exit(0);
}

// Candidate launchers in preference order. Each entry returns the (command, args)
// pair to spawn. We probe via `which`/`where` before exec so a missing launcher
// fails fast instead of dying with ENOENT mid-pipe.
const CANDIDATES = [
  { name: 'uvx', cmd: 'uvx', argv: [PACKAGE_NAME, ...args] },
  { name: 'pipx', cmd: 'pipx', argv: ['run', PACKAGE_NAME, ...args] },
  { name: 'python', cmd: process.platform === 'win32' ? 'python' : 'python3', argv: ['-m', 'sap_datasphere_mcp', ...args] },
];

const which = process.platform === 'win32' ? 'where' : 'which';

function isOnPath(cmd) {
  return new Promise((resolve) => {
    const child = spawn(which, [cmd], { stdio: 'ignore', shell: false });
    child.on('close', (code) => resolve(code === 0));
    child.on('error', () => resolve(false));
  });
}

async function pickLauncher() {
  for (const candidate of CANDIDATES) {
    // eslint-disable-next-line no-await-in-loop
    if (await isOnPath(candidate.cmd)) {
      return candidate;
    }
  }
  return null;
}

async function main() {
  const launcher = await pickLauncher();
  if (!launcher) {
    console.error(
      [
        '',
        `sap-datasphere-mcp (Node wrapper ${VERSION}): could not find a Python launcher.`,
        '',
        'Tried, in order:',
        '  1. uvx       (install: https://docs.astral.sh/uv/)',
        '  2. pipx      (install: https://pipx.pypa.io/)',
        `  3. python3 / python  (then install with: pip install ${PACKAGE_NAME})`,
        '',
        'Pick one of the above and re-run.',
        'Docs: https://github.com/rahulsethi/SAPDatasphereMCP/blob/main/public_docs/INSTALLATION.md',
        '',
      ].join('\n'),
    );
    process.exit(127);
  }

  const child = spawn(launcher.cmd, launcher.argv, {
    stdio: 'inherit',
    shell: false,
    env: process.env,
  });

  child.on('exit', (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exit(code ?? 0);
  });

  child.on('error', (err) => {
    console.error(`sap-datasphere-mcp wrapper: failed to spawn '${launcher.cmd}': ${err.message}`);
    process.exit(1);
  });

  // Forward common termination signals to the child so MCP hosts can shut us down.
  for (const sig of ['SIGINT', 'SIGTERM', 'SIGHUP']) {
    process.on(sig, () => {
      if (!child.killed) child.kill(sig);
    });
  }
}

main().catch((err) => {
  console.error(`sap-datasphere-mcp wrapper: unexpected error: ${err.stack || err}`);
  process.exit(1);
});
