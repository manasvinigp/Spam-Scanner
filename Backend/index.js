const express = require('express');
const bodyParser = require('body-parser');
const { spawn } = require('child_process')
const app = express();
const port = 8080;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
const cors = require('cors');
app.use(cors());


app.get('/endpoint/:id', (req, res) => {
    const receivedUrl= req.params.id; 
    console.log('Received URL:', receivedUrl);
    let result = ''
    const pythonProcess = spawn('python', ['urldetection2.py', receivedUrl]);
    
     pythonProcess.stdout.on('data', (data) => {
        result += data.toString()
        console.log(result)
      });
     
    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`)
        res.status(500).send('Error occurred while running Python script')
      });
      
    pythonProcess.on('close', (code) => {
        if (code === 0) {
           if(result[1]==0){
              
                res.json({ message: "0" });
           }
           else{
            res.json({ message: "1" });
           }
        } else {
          res.status(500).send('Python script exited with an error');
        }
      })
});

app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});