document.getElementById("prediction-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const formData = {
        Item_Identifier: document.getElementById("Item_Identifier").value,
        Item_Weight: parseFloat(document.getElementById("Item_Weight").value),
        Item_Fat_Content: document.getElementById("Item_Fat_Content").value,
        Item_Visibility: parseFloat(document.getElementById("Item_Visibility").value),
        Item_Type: document.getElementById("Item_Type").value,
        Item_MRP: parseFloat(document.getElementById("Item_MRP").value),
        Outlet_Identifier: document.getElementById("Outlet_Identifier").value,
        Outlet_Establishment_Year: parseInt(document.getElementById("Outlet_Establishment_Year").value),
        Outlet_Size: document.getElementById("Outlet_Size").value,
        Outlet_Location_Type: document.getElementById("Outlet_Location_Type").value,
        Outlet_Type: document.getElementById("Outlet_Type").value
    };

    try {
        const response = await fetch("http://127.0.0.1:5001/predict", {


            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        document.getElementById("result").innerText = result.error 
            ? "Error: " + result.error 
            : "📈 Predicted Sales: ₹" + result.Item_Outlet_Sales.toFixed(2);
    } catch (error) {
        document.getElementById("result").innerText = "❌ Server connection failed!";
    }
});

document.getElementById("save-prediction-button").addEventListener("click", async function () {
    const username = localStorage.getItem("username"); // Retrieve the logged-in username
    if (!username) {
        alert("You must be logged in to save predictions.");
        return;
    }

    const formData = {
        username: username,
        Item_Identifier: document.getElementById("Item_Identifier").value,
        Item_Weight: parseFloat(document.getElementById("Item_Weight").value),
        Item_Fat_Content: document.getElementById("Item_Fat_Content").value,
        Item_Visibility: parseFloat(document.getElementById("Item_Visibility").value),
        Item_Type: document.getElementById("Item_Type").value,
        Item_MRP: parseFloat(document.getElementById("Item_MRP").value),
        Outlet_Identifier: document.getElementById("Outlet_Identifier").value,
        Outlet_Establishment_Year: parseInt(document.getElementById("Outlet_Establishment_Year").value),
        Outlet_Size: document.getElementById("Outlet_Size").value,
        Outlet_Location_Type: document.getElementById("Outlet_Location_Type").value,
        Outlet_Type: document.getElementById("Outlet_Type").value,
        // Remove the ₹ symbol and trim the value
        Predicted_Sales: document.getElementById("result").textContent.replace(/[^0-9.]/g, "").trim()
    };

    try {
        const response = await fetch("http://127.0.0.1:5001/save-prediction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        if (response.ok) {
            alert("Prediction saved successfully!");
        } else {
            alert(result.error || "Failed to save prediction.");
        }
    } catch (error) {
        alert("Error connecting to server. Please try again later.");
        console.error("Error saving prediction:", error);
    }
});

document.getElementById("saved-link").addEventListener("click", async function (e) {
    e.preventDefault();

    const username = localStorage.getItem("username"); // Retrieve the logged-in username
    if (!username) {
        alert("You must be logged in to download predictions.");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5001/download-predictions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: username })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status} - ${response.statusText}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${username}_predicted_sales.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        alert("Failed to download the file. Please try again later.");
        console.error("Error downloading file:", error);
    }
});

document.getElementById("login-form").addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!username || !password) {
        alert("Please enter valid credentials.");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:5001/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (response.ok && data.message === "Login successful") {
            // Store the username in localStorage
            localStorage.setItem("username", username);

            // Hide login form and show other sections
            document.getElementById("login-card").style.display = "none";
            document.getElementById("navbar").style.display = "block";
            document.getElementById("footer").style.display = "block";
        } else {
            alert(data.error || "Login failed");
        }
    } catch (error) {
        console.error("Error connecting to server:", error);
        alert("Error connecting to server. Please try again later.");
    }
});

document.getElementById("logout-link").addEventListener("click", function (e) {
    e.preventDefault();

    // Clear the username from localStorage
    localStorage.removeItem("username");

    // Hide all sections and show login form
    document.getElementById("navbar").style.display = "none";
    document.getElementById("main-content").style.display = "none";
    document.getElementById("products-section").style.display = "none";
    document.getElementById("login-card").style.display = "block";
    document.getElementById("login-heading").style.display = "block";
    document.getElementById("register-button").style.display = "block";

    // Reset form fields
    document.getElementById("login-form").reset();
    document.getElementById("register-form").reset();
});
