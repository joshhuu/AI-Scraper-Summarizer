// Format selection handling
        document.querySelectorAll('.format-option').forEach(option => {
            option.addEventListener('click', function () {
                document.querySelectorAll('.format-option').forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
            });
        });

        // Toggle input fields based on selection
        function toggleInputFields() {
            const inputType = document.getElementById("input_type").value;
            document.getElementById("url_input").style.display = inputType === "url" ? "block" : "none";
            document.getElementById("manual_input").style.display = inputType === "manual" ? "block" : "none";
        }

        // Error display function
        function showError(message) {
            const errorDiv = document.getElementById("error-message");
            errorDiv.textContent = message;
            errorDiv.style.display = "block";
            setTimeout(() => errorDiv.style.display = "none", 5000);
        }

        // Show loading state
        function showLoading(show) {
            document.getElementById("loading").style.display = show ? "block" : "none";
        }

        // Form reset function
        function resetForm() {
            document.getElementById("summarizer-form").reset();
            document.getElementById("result-container").style.display = "none";
            document.getElementById("form-container").style.display = "block";
            toggleInputFields();
        }

        // Main form submission handler
        document.getElementById("summarizer-form").addEventListener("submit", async (e) => {
            e.preventDefault();

            if (!document.getElementById("accept").checked) {
                showError("You must accept the disclaimer to proceed");
                return;
            }

            const formatType = document.querySelector('.format-option.selected').dataset.format;
            const inputType = document.getElementById("input_type").value;

            const requestData = {
                accept_disclaimer: true,
                input_type: inputType,
                format: formatType
            };

            if (inputType === "url") {
                requestData.url = document.getElementById("url").value.trim();
                if (!requestData.url) {
                    showError("Please enter a valid URL");
                    return;
                }
            } else {
                requestData.manual = document.getElementById("manual").value.trim();
                if (!requestData.manual) {
                    showError("Please enter some content to summarize");
                    return;
                }
                // Add to form submission handler
                if (!sessionStorage.getItem('agreementAccepted')) {
                    if (!document.getElementById("accept").checked) {
                        showError("You must accept the disclaimer to proceed");
                        return;
                    }
                    sessionStorage.setItem('agreementAccepted', 'true');
                }

                // Add to initial setup
                if (sessionStorage.getItem('agreementAccepted')) {
                    document.querySelector('.disclaimer').style.display = 'none';
                    document.querySelector('.checkbox-group').style.display = 'none';
                }

            }
            document.getElementById("url").addEventListener("input", function (e) {
                const isValid = isValidUrl(e.target.value);
                e.target.style.borderColor = isValid ? "#4CAF50" : "#ff4444";
            });
            document.getElementById("manual").addEventListener("input", function (e) {
                const charCount = e.target.value.length;
                document.getElementById("char-counter").textContent =
                    `${charCount} characters | ~${Math.round(charCount / 5)} words`;
            });
            try {
                showLoading(true);
                const response = await fetch('http://localhost:5000/api/summarize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'Failed to generate summary');
                }

                document.getElementById("summary").innerHTML = data.summary;
                document.getElementById("form-container").style.display = "none";
                document.getElementById("result-container").style.display = "block";
            } catch (error) {
                showError(error.message);
            } finally {
                showLoading(false);
            }
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') resetForm();
        });
        // Initial setup
        toggleInputFields();