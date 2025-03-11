// This file disables static generation for all pages
export const config = {
  unstable_runtimeJS: true,
  unstable_JsPreload: false
}

// Export a dummy function to make this a valid module
export default function Config() {
  return null;
} 