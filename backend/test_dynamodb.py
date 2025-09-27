
import asyncio
async def test_dynamodb():
    try:
        print("Testing DynamoDB connection...")

        from app.database.dynamodb import DynamoDBConnection

        db = DynamoDBConnection()

        if await db.test_connection():
            print(" DynamoDB connection successful!")

            if db.create_tables():
                print(" Tables created successfully!")
            else:
                print(" Table creation failed!")
        else:
            print(" DynamoDB connection failed!")

    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_dynamodb())