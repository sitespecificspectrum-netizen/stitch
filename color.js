// 색 비교: sRGB → CIELAB, 사람 눈 기준 색 차이(CIEDE2000)로 가장 비슷한 DMC 실을 찾는다.

function hexToRgb(hex) {
  const v = parseInt(hex, 16);
  return [(v >> 16) & 255, (v >> 8) & 255, v & 255];
}
function rgbToHex([r, g, b]) {
  return ((1 << 24) | (r << 16) | (g << 8) | b).toString(16).slice(1).toUpperCase();
}

function rgbToLab([r, g, b]) {
  const lin = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  const R = lin(r), G = lin(g), B = lin(b);
  const X = (R * 0.4124 + G * 0.3576 + B * 0.1805) / 0.95047;
  const Y = (R * 0.2126 + G * 0.7152 + B * 0.0722) / 1.0;
  const Z = (R * 0.0193 + G * 0.1192 + B * 0.9505) / 1.08883;
  const f = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
  const fx = f(X), fy = f(Y), fz = f(Z);
  return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
}

function deltaE2000([L1, a1, b1], [L2, a2, b2]) {
  const rad = Math.PI / 180, deg = 180 / Math.PI;
  const C1 = Math.hypot(a1, b1), C2 = Math.hypot(a2, b2), Cb = (C1 + C2) / 2;
  const G = 0.5 * (1 - Math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)));
  const a1p = a1 * (1 + G), a2p = a2 * (1 + G);
  const C1p = Math.hypot(a1p, b1), C2p = Math.hypot(a2p, b2);
  const hue = (b, a) => { if (a === 0 && b === 0) return 0; const h = Math.atan2(b, a) * deg; return h < 0 ? h + 360 : h; };
  const h1p = hue(b1, a1p), h2p = hue(b2, a2p);
  const dLp = L2 - L1, dCp = C2p - C1p;
  let dhp = 0;
  if (C1p * C2p !== 0) { dhp = h2p - h1p; if (dhp > 180) dhp -= 360; else if (dhp < -180) dhp += 360; }
  const dHp = 2 * Math.sqrt(C1p * C2p) * Math.sin((dhp / 2) * rad);
  const Lbp = (L1 + L2) / 2, Cbp = (C1p + C2p) / 2;
  let hbp = h1p + h2p;
  if (C1p * C2p !== 0) {
    hbp = Math.abs(h1p - h2p) > 180 ? (h1p + h2p < 360 ? (h1p + h2p + 360) / 2 : (h1p + h2p - 360) / 2) : (h1p + h2p) / 2;
  }
  const T = 1 - 0.17 * Math.cos((hbp - 30) * rad) + 0.24 * Math.cos(2 * hbp * rad)
    + 0.32 * Math.cos((3 * hbp + 6) * rad) - 0.2 * Math.cos((4 * hbp - 63) * rad);
  const dTh = 30 * Math.exp(-(((hbp - 275) / 25) ** 2));
  const Rc = 2 * Math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7));
  const Sl = 1 + (0.015 * (Lbp - 50) ** 2) / Math.sqrt(20 + (Lbp - 50) ** 2);
  const Sc = 1 + 0.045 * Cbp, Sh = 1 + 0.015 * Cbp * T;
  const Rt = -Math.sin(2 * dTh * rad) * Rc;
  return Math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2 + Rt * (dCp / Sc) * (dHp / Sh));
}

// DMC 실마다 Lab을 미리 계산해 둔다 (같은 색인 White/BLANC 등은 첫 번째만 추천 대상)
const DMC_LAB = (() => {
  const seen = new Set();
  return DMC.filter(([, , hex]) => (seen.has(hex) ? false : seen.add(hex)))
    .map(([code, , hex]) => ({ code, lab: rgbToLab(hexToRgb(hex)) }));
})();

/** hex 색과 가장 가까운 실. codes를 주면 그 안에서만 찾는다. */
function nearestThread(hex, codes) {
  const lab = rgbToLab(hexToRgb(hex));
  const pool = codes ? DMC_LAB.filter((t) => codes.has(t.code)) : DMC_LAB;
  let best = null;
  for (const t of pool) {
    const d = deltaE2000(lab, t.lab);
    if (!best || d < best.dE) best = { code: t.code, dE: d };
  }
  return best;
}

function colorDistance(hexA, hexB) {
  return deltaE2000(rgbToLab(hexToRgb(hexA)), rgbToLab(hexToRgb(hexB)));
}

function similarityLabel(dE) {
  if (dE < 3) return '거의 같은 색';
  if (dE < 7) return '비슷한 색';
  if (dE < 12) return '조금 다른 색';
  return '많이 다른 색';
}

/** 글자를 얹었을 때 잘 보이는 색 */
function inkFor(hex) {
  const [r, g, b] = hexToRgb(hex);
  return 0.299 * r + 0.587 * g + 0.114 * b > 150 ? '#1c1c1e' : '#ffffff';
}
