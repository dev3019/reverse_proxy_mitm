const express = require("express");

const app = express();
app.use(express.json());


app.post("/post", (req, res) => {
    console.log('headers:', req.headers)
    console.log("API received:", req.body);

    res.json({
        status: "ok",
        message: "static response",
        echo: req.body,
    });
});
app.listen(3000, () => {
    console.log("Node API listening on 3000");
});
