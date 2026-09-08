/** Prim SDK — TypeScript. The primitives of Prim itself. */

export { parse, split, type Face, type FaceMap, type FaceValue } from "./face.ts";
export {
  BASE_REQUIRED,
  Pack,
  PrimError,
  TAR_SUFFIXES,
  ZIP_SUFFIXES,
  openPrim,
  type PackFiles,
  type PackPair,
  type PackSource,
} from "./pack.ts";
export {
  CONSTRAINT_FACE_KEYS,
  IDENTITY_FACE_KEYS,
  LOG_FACE_KEYS,
  PRIMITIVE_NAMES,
  PRIMITIVES,
  PROJECTION_FACE_KEYS,
  primitive,
  type Primitive,
} from "./primitives.ts";
export { TRUST_ORDER, trustTier, type TrustTier } from "./trust.ts";
export {
  FACE_VIEW,
  createView,
  registerView,
  resolveView,
  viewKey,
  type View,
} from "./ui.ts";
export {
  TOOL_DIRECTIONS,
  TOOL_KINDS,
  counterpartOf,
  createTool,
  isToolDirection,
  isToolKind,
  type PrimTool,
  type ToolCounterpart,
  type ToolDirection,
  type ToolKind,
} from "./tools.ts";
export {
  createValidator,
  registerValidator,
  validate,
  validators,
  type Validator,
} from "./validator.ts";
export {
  getApplet,
  getTool,
  getType,
  listApplets,
  listTools,
  listTypes,
  loadRegistry,
  registerApplet,
  registerTool,
  registerType,
  registry,
  resetRegistry,
  type PrimApplet,
  type PrimType,
  type RegisteredTool,
  type Registry,
  type TypeStatus,
} from "./registry.ts";

export const VERSION = "0.5.0-dev.1";

export { ProfileLibrary, ProfileError, parseProfileJSON, type DefinitionPin, type CreationKit, type JSONValue, type ProfileProblem } from "./profile-library.ts";
