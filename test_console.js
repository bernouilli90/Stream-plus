// Test script for execute all rules API
// Run this in the browser console on http://localhost:5000

async function testExecuteAllRules() {
    console.log('Testing execute all rules API...');

    const requestData = { stream: true };
    console.log('Request data:', requestData);
    console.log('JSON stringified:', JSON.stringify(requestData));

    try {
        const response = await fetch('http://localhost:5000/api/sorting-rules/execute-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        console.log('Response status:', response.status);
        console.log('Response status text:', response.statusText);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        console.log('Response ok:', response.ok);

        if (!response.ok) {
            console.error('Response not ok!');
            const responseText = await response.text();
            console.log('Response text:', responseText);
            return;
        }

        const result = await response.json();
        console.log('Success! Response:', result);

    } catch (error) {
        console.error('Error:', error);
    }
}

// Run the test
testExecuteAllRules();