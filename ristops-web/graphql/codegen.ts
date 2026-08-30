import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  schema: './graphql/schema.gql',
  documents: './src/**/*.graphql',
  generates: {
    './src/services/graphql/': {
      preset: 'client',
      presetConfig: {
        // The app reads query results directly; nothing uses `useFragment`, so masking would
        // only hide the fields of the one shared fragment behind a cast.
        fragmentMasking: false,
      },
      config: {
        scalars: {
          DateTime: 'string',
          Time: 'string',
          Date: 'string',
        },
        useTypeImports: true,
        enumsAsConst: true,
      },
    },
  },
};

export default config;
