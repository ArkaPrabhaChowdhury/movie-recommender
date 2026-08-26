import ApiService from './api';

const contentSchema = {
  type: 'object',
  properties: {
    content_id: { type: 'integer', description: 'TMDB content ID' },
    content_type: { type: 'string', enum: ['movie', 'tv'], description: 'movie or TV show' },
    title: { type: 'string', description: 'Title, used to confirm the action in the result' }
  },
  required: ['content_id', 'content_type'],
  additionalProperties: false
};

const summarizeTitle = (item) => ({
  id: item.id,
  content_type: item.content_type,
  title: item.title || item.name,
  overview: item.overview || '',
  rating: item.rating ?? item.vote_average ?? null,
  release_date: item.release_date || item.first_air_date || '',
  genres: Array.isArray(item.genres)
    ? item.genres.map((genre) => typeof genre === 'string' ? genre : genre.name).filter(Boolean)
    : [],
  poster: item.poster || item.poster_path || null
});

const getDetails = async ({ content_id, content_type }) => {
  const details = await ApiService.getDetails(content_type, content_id);
  return summarizeTitle({ ...details, content_type });
};

const getActionItem = async (input) => {
  const details = await ApiService.getDetails(input.content_type, input.content_id);
  return { ...details, content_type: input.content_type };
};

const result = (message, data = {}) => ({
  message,
  ...data
});

/**
 * Registers OTT Scout's real product capabilities with the WebMCP browser API.
 * The API is experimental, so the app remains fully usable in browsers without it.
 */
export const registerWebMCPTools = (getApi) => {
  const modelContext = typeof document !== 'undefined' ? document.modelContext : null;
  if (!modelContext?.registerTool) return () => {};
  const controller = new AbortController();

  const tools = [
    {
      name: 'search_movies',
      description: 'Search OTT Scout for movies and TV shows by title, actor, genre, or keyword.',
      inputSchema: {
        type: 'object',
        properties: { query: { type: 'string', minLength: 1, description: 'What to search for' } },
        required: ['query'],
        additionalProperties: false
      },
      annotations: { readOnlyHint: true },
      execute: async ({ query }) => {
        if (!query?.trim()) return result('Please provide a search query.', { results: [] });
        const data = await ApiService.globalSearch(query.trim());
        const results = (data.content || []).map(summarizeTitle);
        return result(`Found ${results.length} title(s) for “${query.trim()}”.`, { results });
      }
    },
    {
      name: 'get_movie_details',
      description: 'Get plot, rating, cast, trailers, and streaming information for a movie or TV show.',
      inputSchema: contentSchema,
      annotations: { readOnlyHint: true },
      execute: getDetails
    },
    {
      name: 'get_recommendations',
      description: 'Get personalized OTT recommendations based on the user profile and an optional mood or request.',
      inputSchema: {
        type: 'object',
        properties: {
          mood: { type: 'string', description: 'Optional mood, such as cozy, intense, or funny' },
          specific_request: { type: 'string', description: 'Optional natural-language request' },
          limit: { type: 'integer', minimum: 1, maximum: 20, description: 'Maximum number of results' }
        },
        additionalProperties: false
      },
      annotations: { readOnlyHint: true },
      execute: async ({ mood, specific_request, limit = 10 } = {}) => {
        const { userId } = getApi();
        if (!userId) return result('A user profile is still loading. Try again in a moment.', { results: [] });
        const data = await ApiService.getPersonalizedRecommendations(userId, {
          mood,
          specificRequest: specific_request,
          limit
        });
        const recommendations = (data.recommendations || []).map(summarizeTitle);
        return result(`Found ${recommendations.length} personalized recommendation(s).`, {
          personalization_level: data.personalization_level || 'none',
          results: recommendations
        });
      }
    },
    {
      name: 'find_streaming_options',
      description: 'Find streaming platforms where a movie or TV show is available in a region.',
      inputSchema: {
        type: 'object',
        properties: {
          content_id: { type: 'integer', description: 'TMDB content ID' },
          content_type: { type: 'string', enum: ['movie', 'tv'] },
          region: { type: 'string', pattern: '^[A-Z]{2}$', description: 'ISO country code, default IN', default: 'IN' }
        },
        required: ['content_id', 'content_type'],
        additionalProperties: false
      },
      annotations: { readOnlyHint: true },
      execute: async ({ content_id, content_type, region = 'IN' }) => {
        const details = await ApiService.getDetails(content_type, content_id);
        const available = details.streaming?.available_on || [];
        return result(
          available.length ? `${details.title} is available on ${available.map((p) => p.name).join(', ')}.` : `No streaming options found for ${details.title}.`,
          { title: details.title, region, platforms: available }
        );
      }
    },
    ...[
      ['add_to_watchlist', 'Add a movie or TV show to the user’s OTT Scout watchlist.', 'addToWatchlist', 'watchlisted'],
      ['mark_as_watched', 'Mark a movie or TV show as watched in the user’s OTT Scout history.', 'markAsWatched', 'watched'],
      ['like_title', 'Like a movie or TV show to improve future personalized recommendations.', 'likeContent', 'liked']
    ].map(([name, description, actionKey, actionName]) => ({
      name,
      description,
      inputSchema: contentSchema,
      annotations: { readOnlyHint: false },
      execute: async (input) => {
        const api = getApi();
        const action = api[actionKey];
        const { userId } = api;
        if (!userId) return result('A user profile is still loading. Try again in a moment.');
        if (typeof action !== 'function') return result('This action is not available yet. Try again in a moment.');
        const item = await getActionItem(input);
        const saved = await action(item);
        return result(saved ? `${item.title} was ${actionName === 'watchlisted' ? 'added to your watchlist' : actionName}.` : `Unable to update ${item.title}.`, {
          title: item.title,
          content_id: input.content_id,
          content_type: input.content_type,
          action: actionName,
          success: Boolean(saved)
        });
      }
    }))
  ];

  tools.forEach((tool) => {
    Promise.resolve(modelContext.registerTool(tool, { signal: controller.signal })).catch((error) => {
      if (error?.name !== 'AbortError') console.warn(`Unable to register WebMCP tool ${tool.name}:`, error);
    });
  });

  return () => controller.abort();
};
