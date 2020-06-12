class DBHelper():
    async def insert_db(self, collection, data):
        user = await collection.insert_one(data)
        return user

    async def async_select_db(self, collection, data):
        user = await collection.find_one(data)
        return user

    async def update_row(self, collection, row_ident, data):
        return await collection.update_one(row_ident, data)

    async def delete_row(self, collection, row_ident):
        return await collection.delete_one(row_ident)