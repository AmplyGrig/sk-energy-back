class DBHelper():
    async def _insert_db(self, collection, data):
        return await collection.insert_one(data)

    async def _select_db(self, collection, data, proection=None):
        return await collection.find_one(data, proection)

    async def _find_db(self, collection, data, proection=None):
        res_arr = []
        async for document in collection.find(data, proection):
            res_arr.append(document)
        return res_arr

    async def _update_db(self, collection, row_ident, data):
        return await collection.update_one(row_ident, data)

    async def _delete_db(self, collection, row_ident):
        return await collection.delete_one(row_ident)

    async def _aggregate(self, collection, pipeline):
        res_arr = []
        async for document in collection.aggregate(pipeline):
            res_arr.append(document)
        return res_arr