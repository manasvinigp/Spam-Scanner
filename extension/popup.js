chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const tabUrl = tabs[0].url;
    console.log("URL of the active tab:", tabUrl);

    const url = `http://localhost:8080/endpoint/${encodeURIComponent(tabUrl)}`;

    console.log(url);

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Response from server:', data);
            console.log(data.message);

            const insscanning = document.querySelector('.insidescanning');
            const lt = document.querySelector(".loading-paragraph");
            let im;

            if (parseFloat(data.message) === 0) {
                im = document.createElement("img");
                im.setAttribute("src", "correct.jpg");
                im.classList.add("correctimage");
                lt.classList.add("greencolor");
                lt.innerHTML = "Safe To Proceed!";
            } else {
                im = document.createElement("img");
                im.setAttribute("src", "wrong.jpg");
                im.classList.add("wrongimage");
                lt.classList.add("redcolor");
                lt.innerHTML = "Suspicious Link, STAY AWAY!";
            }
            

            const spanElement = insscanning.querySelector("span");
            if (spanElement) {
                insscanning.removeChild(spanElement);
            }
            insscanning.appendChild(im);

            // Update progress bar based on accuracy rate
            const progressBar = document.querySelector('.progress-bar');
            const accuracyRate = parseInt(data.accuracyRate, 10); // Assuming the accuracy rate is provided in the data

            progressBar.style.width = accuracyRate + '%';

            if (data.message === '0') {
                progressBar.style.backgroundColor = '#28a745'; // Green color
            } else {
                progressBar.style.backgroundColor = '#f30a0a'; // Red color
            }
        })
        .catch(error => {
            console.error('There was a problem with your fetch operation:', error);
        });

    document.addEventListener('DOMContentLoaded', function() {
        const generateReportBtn = document.getElementById('generateReportBtn');

        function isMaliciousSite(data) {
            return data.message !== '0';
        }

        function updateButtonState(data) {
            generateReportBtn.disabled = isMaliciousSite(data);
            generateReportBtn.classList.toggle('inactive', !generateReportBtn.disabled);
        }
        
        fetch('otherFile.js')
         .then(response => response.text())
  .then(scriptText => {
    const scriptElement = document.createElement('script');
    scriptElement.textContent = scriptText;
    document.body.appendChild(scriptElement);
  });

    function generateReport() {
    alert('Generating report...');
      setTimeout(function() {
        alert('Report generated!');
        const reportUrl = 'C:/Manasvini/WebDev/NMIThacksv3/Backend/outputfeedback.pdf'; // Replace with the actual URL or path to your generated PDF report
        window.open(reportUrl, '_blank'); // Open the generated PDF report in a new window/tab
      }, 6000);
    }

        generateReportBtn.addEventListener('click', generateReport);

        fetch(url)
            .then(response => response.json())
            .then(data => {
                updateButtonState(data);
            })
            .catch(error => {
                console.error('There was a problem with your fetch operation:', error);
            });

        const progressBar = document.querySelector('.progress-bar');
        progressBar.style.backgroundColor = '#FFFFFF'; // Set initial color to white
        progressBar.style.width = '100%'; // Set width to full for visual consistency

        const textPrompts = document.querySelector('.text-prompts');
        const promptHeading = textPrompts.querySelector('.prompt-heading');
        

        const pythonProcess = spawn('python', ['llm.py', receivedUrl]);
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
          });
        const filePath = 'output.txt';
        fetchParagraphFromFile(filePath)
        .then(paragraph => {
        // Update the text content of promptHeading with the paragraph content
        promptHeading.textContent = paragraph;
        })
        .catch(error => console.error('Error:', error));
        

    });
        
    });

