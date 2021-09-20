import _ from "lodash";
import { getElasticClient } from "@/config/elastic";

export const schemaConfig = {
  title: "text",
  subtitle: "text",
  short_description: "text",
  description: "text",
  brand: "text",

  valid_from: "date",
  valid_through: "date",

  price: "number",
  pre_price: "number",

  dealer: "text",

  standard_value: "number",
  standard_size: "number",

  gtins: "text",
  categories: "text",

  mpn_properties: "text",

  nutrition_carbohydrates: "number",
  nutrition_proteins: "number",
  nutrition_fats: "number",
  nutrition_energy: "number",
  nutrition_fibers: "number",
};

export const getSchemaElasticClient =
  async (): Promise<ISchemaElasticClient> => {
    const elasticClient: ISchemaElasticClient =
      (await getElasticClient()) as ISchemaElasticClient;

    function listSchema(engineName) {
      return this.client.get(
        `engines/${encodeURIComponent(engineName)}/schema`,
      );
    }
    function listSettings(engineName) {
      return this.client.get(
        `engines/${encodeURIComponent(engineName)}/search_settings`,
      );
    }
    function updateSchema(engineName, schemaConfig) {
      return this.client.post(
        `engines/${encodeURIComponent(engineName)}/schema`,
        schemaConfig,
      );
    }
    function updateSettings(engineName, settingsConfig) {
      return this.client.put(
        `engines/${encodeURIComponent(engineName)}/search_settings`,
        settingsConfig,
      );
    }
    elasticClient.listSchema = listSchema.bind(elasticClient);
    elasticClient.listSettings = listSettings.bind(elasticClient);
    elasticClient.updateSchema = updateSchema.bind(elasticClient);
    elasticClient.updateSettings = updateSettings.bind(elasticClient);

    return elasticClient;
  };

export const ensureEngineExists = async (engineName: string) => {
  const elasticClient = await getElasticClient();
  const { results: elasticEngines } = await elasticClient.listEngines();
  console.log("Existing elastic engines:");
  console.log(elasticEngines);
  if (!elasticEngines.find(({ name }) => name === engineName)) {
    console.info(`Did not find existing engine ${engineName}. Creating it.`);
    const createEngineResponse = await elasticClient.createEngine(engineName, {
      language: null,
    });
    console.info(createEngineResponse);
  } else {
    console.info(`Found existing engine ${engineName}.`);
  }
};

export const ensureOfferSchema = async (engineName: string) => {
  const elasticClient = await getSchemaElasticClient();

  const settingsConfig = {
    title: { weight: 3 },
    categories: { weight: 2 },
    dealer: { weight: 1 },
    brand: { weight: 1 },
    subtitle: { weight: 1 },
    short_description: { weight: 1 },
    description: { weight: 1 },
    gtins: { weight: 1 },
  };

  await ensureEngineExists(engineName);

  const existingSchema = await elasticClient.listSchema(engineName);
  console.log("Existing schema:");
  console.log(existingSchema);
  if (_.isEqual(existingSchema, schemaConfig)) {
    console.log(`Schema in ${engineName} is already configured correctly.`);
  } else {
    console.log(`Configuring schema in ${engineName}.`);
    const updateSchemaResult = await elasticClient.updateSchema(
      engineName,
      schemaConfig,
    );
    console.log(`Updated schema in ${engineName}.`);
    console.log(updateSchemaResult);
  }

  const existingSettings = await elasticClient.listSettings(engineName);
  console.log("Exisiting settings:");
  console.log(existingSettings);
  const updateSettingsResult = await elasticClient.updateSettings(engineName, {
    search_fields: settingsConfig,
  });
  console.log(`Updated settings in ${engineName}.`);
  console.log(updateSettingsResult);
};
