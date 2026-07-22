import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  schema: './graphql/schema.gql',
  documents: './src/**/*.graphql',
  generates: {
    './src/services/graphql/': {
      preset: 'client',
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
