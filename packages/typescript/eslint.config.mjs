import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist/**", "src/generated/**"] },
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // fetch().json() returns unknown; type assertions against unknown are
      // the accepted pattern for external API responses without a schema lib.
      "@typescript-eslint/no-unsafe-type-assertion": "off",
      // Numbers in HTTP status / error messages are idiomatic and safe.
      "@typescript-eslint/restrict-template-expressions": [
        "error",
        { allowNumber: true },
      ],
    },
  }
);
