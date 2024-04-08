require('dotenv').config();
const express = require('express');
const { MongoClient } = require('mongodb');

const app = express();
const port = process.env.PORT
const cors = require('cors');
app.use(cors());
const uri = process.env.MONGODB_URI;

//Query para traer los documentos de ese día y si no los del último
app.get('/', async (req, res) => {
    const client = new MongoClient(uri);
    try {
        await client.connect();
        const database = client.db("papyrus");
        const collection = database.collection("BOE");

        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1; // getMonth() is zero-based, add 1 for 1-12 scale
        const day = today.getDate();

        let data = await collection.find({ anio: year, mes: month, dia: day }).toArray();

        if (data.length === 0) {
            // If no documents are found for today, find the most recent date with documents
            const latestDocument = await collection.find({})
                .sort({anio: -1, mes: -1, dia: -1})
                .limit(1)
                .toArray();

            if (latestDocument.length > 0) {
                // Use the date from the latest document to fetch all documents for that date
                data = await collection.find({
                    anio: latestDocument[0].anio,
                    mes: latestDocument[0].mes,
                    dia: latestDocument[0].dia
                }).toArray();
            }
        }

        res.json(data);
    } catch (error) {
        console.error("Failed to retrieve data:", error);
        res.status(500).send("Error retrieving data from database.");
    } finally {
        await client.close();
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
