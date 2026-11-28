// Big Shoulders Display's package exports its weights without the .css suffix
// ("@fontsource/big-shoulders-display/800"), which TypeScript's "*.css" rule can't see.
declare module "@fontsource/big-shoulders-display/*";
