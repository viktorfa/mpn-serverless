interface IElasticClient {
  post(path: string, params: object);
}

interface AppSearchParams {
  page?: {
    size?: number;
    current?: number;
    search_fields?: Record<string, number>;
  };
  filters?: Record<
    string,
    string[] | { from?: string | number | Date; to?: string | number | Date }
  >;
}

interface AppSearchEngine {
  name: string;
}

interface IAppSearchClient {
  search<T>(
    engineName: string,
    query: string,
    options?: AppSearchParams,
  ): ElasticResponse<T>;
  querySuggestion(
    engineName: string,
    query: string,
    options?: Record<string, any>, // Not sure what valid options here are.
  ): ElasticQuerySuggestionResponse;
  client: IElasticClient;
  listEngines(): Promise<{ results: AppSearchEngine[] }>;
  createEngine(engineName: string, options: { language: string | null });
}

interface ElasticResponse<T> {
  meta: {
    alerts: [];
    warnings: [];
    page: {
      current: number;
      total_pages: number;
      total_results: number;
      size: number;
    };
    engine: { name: string; type: string };
    request_id: string;
  };
  results: T[];
}
interface ElasticQuerySuggestionResponse {
  meta: {
    request_id: string;
  };
  results: { documents: { ["suggestion"]: string }[] };
}

interface ISchemaElasticClient extends IAppSearchClient {
  listSchema(engineName: string);
  updateSchema(engineName: string, schemaConfig: Record<string, string>);
  listSettings(engineName: string);
  updateSettings(
    engineName: string,
    settingsConfig: { search_fields: Record<string, { weight: number }> },
  );
}

type SchemaFieldType = "text" | "number" | "geolocation" | "date";
