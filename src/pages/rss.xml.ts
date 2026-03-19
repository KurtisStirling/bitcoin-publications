import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const bitcoin = await getCollection('bitcoin');

  const items = bitcoin
    .sort((a, b) => new Date(b.data.date).getTime() - new Date(a.data.date).getTime())
    .map(pub => ({
      title: pub.data.title,
      pubDate: new Date(pub.data.date),
      description: pub.data.description,
      link: `/bitcoin/${pub.id}/`,
    }));

  return rss({
    title: 'Kurtis Stirling',
    description: 'Bitcoin research, business analysis, and independent thinking.',
    site: context.site ?? 'https://kurtisstirling.com',
    items,
  });
}
