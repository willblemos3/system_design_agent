# =========================
# milvus_store.py
# =========================

from pymilvus import (
    MilvusClient,
    DataType,
    FieldSchema,
    CollectionSchema,
)

from src.foundation.vector_store.vector_store import (
    VectorStore,
    VectorRecord,
    SearchResult,
)


TYPE_MAPPING = {
    "string": DataType.VARCHAR,
    "int64": DataType.INT64,
    "vector": DataType.FLOAT_VECTOR,
    "json": DataType.JSON,
}


class MilvusVectorStore(VectorStore):

    def __init__(
        self,
        db_path="./milvus_workshop.db",
    ):
        self.client = MilvusClient(db_path)


    def create_index(
        self,
        index_name: str,
        schema: dict,
    ):

        fields = []

        for field in schema["fields"]:

            kwargs = {
                "name": field["name"],
                "dtype": TYPE_MAPPING[field["type"]],
            }

            if field["type"] == "string":
                kwargs["max_length"] = field["max_length"]

            if field["type"] == "vector":
                kwargs["dim"] = field["dim"]

            if field.get("primary"):
                kwargs["is_primary"] = True
                kwargs["auto_id"] = field.get(
                    "auto_id",
                    False,
                )

            fields.append(
                FieldSchema(**kwargs)
            )


        collection_schema = CollectionSchema(
            fields,
            description=schema["description"],
        )


        try:
            self.client.drop_collection(
                index_name
            )
        except Exception:
            pass


        self.client.create_collection(
            collection_name=index_name,
            schema=collection_schema,
        )


        index_params = self.client.prepare_index_params(
            field_name=schema["vector_field"],
            index_type="AUTOINDEX",
            metric_type=schema["metric_type"],
        )


        self.client.create_index(
            collection_name=index_name,
            index_params=index_params,
        )


        self.client.load_collection(
            collection_name=index_name,
        )


    def insert(
      self,
      index_name: str,
      records,
  ):

      rows = []

      for record in records:

          row = dict(
              record.metadata
          )

          rows.append(
              row
          )


      self.client.insert(
          collection_name=index_name,
          data=rows,
      )


      self.client.flush(
          index_name
    )


    def search(
        self,
        index_name: str,
        query_vector,
        top_k: int,
    ):

        results = self.client.search(
            collection_name=index_name,

            data=[query_vector],

            limit=top_k,

            search_params={
                "metric_type": "COSINE",
            },

            output_fields=["*"],
        )


        formatted = []

        for hit in results[0]:

            entity = hit["entity"]

            record_id = (
                entity.get("candidate_id")
                or entity.get("id")
            )


            formatted.append(
                SearchResult(
                    id=str(record_id),

                    score=float(
                        hit["distance"]
                    ),

                    metadata=dict(
                        entity
                    ),
                )
            )


        return formatted