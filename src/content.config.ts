import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const bitcoin = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/bitcoin' }),
  schema: z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    date: z.string(),
    tags: z.array(z.string()).default([]),
    status: z.enum(['draft', 'published']).default('draft'),
    description: z.string(),
    type: z.enum(['paper', 'bip', 'essay']),
  }),
});

export const collections = { bitcoin };
