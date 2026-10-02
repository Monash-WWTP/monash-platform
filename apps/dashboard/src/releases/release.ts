import manifest from "./current.json";
export interface Release {
  versionName: string;
  versionCode: number;
  notes: string[];
  minAndroid: string;
  publishedAt: string;
  byteSize: number;
  sha256: string;
  artifactUrl: string;
}
export function parseRelease(input: unknown): Release | null {
  if (!input || typeof input !== "object") return null;
  const r = input as Record<string, unknown>;
  if (
    !Array.isArray(r.notes) ||
    !r.notes.length ||
    !r.notes.every((n) => typeof n === "string" && n.trim().length > 0) ||
    typeof r.versionName !== "string" ||
    !/^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?$/.test(r.versionName) ||
    !Number.isSafeInteger(r.versionCode) ||
    Number(r.versionCode) <= 0 ||
    !Number.isSafeInteger(r.byteSize) ||
    Number(r.byteSize) <= 0 ||
    typeof r.minAndroid !== "string" ||
    !/^\d+(?:\.\d+)*$/.test(r.minAndroid) ||
    typeof r.publishedAt !== "string" ||
    !/^\d{4}-\d{2}-\d{2}$/.test(r.publishedAt) ||
    !Number.isFinite(Date.parse(r.publishedAt)) ||
    new Date(r.publishedAt).toISOString().slice(0, 10) !== r.publishedAt ||
    typeof r.sha256 !== "string" ||
    !/^[a-f0-9]{64}$/.test(r.sha256) ||
    typeof r.artifactUrl !== "string"
  )
    return null;
  try {
    const u = new URL(r.artifactUrl);
    if (
      u.protocol !== "https:" ||
      u.username ||
      u.password ||
      ["github.com", "api.github.com"].includes(u.hostname) ||
      !u.pathname.endsWith(".apk") ||
      u.hash
    )
      return null;
  } catch {
    return null;
  }
  return {
    versionName: r.versionName,
    notes: r.notes as string[],
    versionCode: Number(r.versionCode),
    minAndroid: r.minAndroid,
    publishedAt: r.publishedAt,
    byteSize: Number(r.byteSize),
    sha256: r.sha256,
    artifactUrl: r.artifactUrl,
  };
}
// Derived from the verified, publicly hosted signed artifact.
export const currentRelease = parseRelease(manifest);
