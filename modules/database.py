class DBHelper():
    async def insert_db(self, collection, data):
        user = await collection.insert_one(data)
        return user

    async def async_select_db(self, collection, data, proection=None):
        user = await collection.find_one(data, proection)
        return user

    async def do_find(self, collection, data, proection=None):
        res_arr = []
        async for document in collection.find(data, proection):
            res_arr.append(document)
        return res_arr

    async def update_row(self, collection, row_ident, data):
        return await collection.update_one(row_ident, data)

    async def delete_row(self, collection, row_ident):
        return await collection.delete_one(row_ident)