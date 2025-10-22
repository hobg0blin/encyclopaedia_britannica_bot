import { BskyAgent } from '@atproto/api';
import * as dotenv from 'dotenv';
import { CronJob } from 'cron';
import * as process from 'process';
import * as fs from 'fs';
import * as path from 'path';
import encyclopedia from './output.json';

dotenv.config();

// Create a Bluesky Agent
const agent = new BskyAgent({
    service: 'https://atproto.bront.rodeo',
  })

const INDEX_FILE = path.join(__dirname, 'current_index.txt');

// Flatten all entries from all pages into a single array
const allEntries = encyclopedia.flatMap(page => page.entries);

function getCurrentIndex(): number {
    try {
        if (fs.existsSync(INDEX_FILE)) {
            const content = fs.readFileSync(INDEX_FILE, 'utf-8');
            return parseInt(content.trim(), 10) || 0;
        }
    } catch (error) {
        console.error('Error reading index file:', error);
    }
    return 0;
}

function saveCurrentIndex(index: number): void {
    try {
        fs.writeFileSync(INDEX_FILE, index.toString(), 'utf-8');
    } catch (error) {
        console.error('Error saving index file:', error);
    }
}

async function main() {
    // Get the current index
    const currentIndex = getCurrentIndex();

    // Check if we have entries to post
    if (allEntries.length === 0) {
        console.log('No entries found in encyclopedia');
        return;
    }

    // Get the current entry (wrap around if we've reached the end)
    const entry = allEntries[currentIndex % allEntries.length];

    console.log(`Posting entry ${currentIndex + 1} of ${allEntries.length}`);
    console.log(`Title: ${entry.title}`);
    console.log(`Text: ${entry.text.substring(0, 100)}...`);

    // Post to Bluesky
    await agent.login({ identifier: process.env.BLUESKY_USERNAME!, password: process.env.BLUESKY_PASSWORD!});
    await agent.post({
        text: `${entry.text}`
    });

    // Increment and save the index for next time
    saveCurrentIndex(currentIndex + 1);

    console.log('Posted successfully!');
}

main();


// Run this on a cron job
const scheduleExpression5Seconds = '*/5 * * * * *'; // Run every 5 seconds for testing                 ╎│
const scheduleExpressionMinute = '* * * * *'; // Run once every minute for testing
const scheduleExpression20Minutes ='*/20 * * * *'; // Run once every 20 minutes for testing
const scheduleExpression = '0 */3 * * *'; // Run once every three hours in prod

const job = new CronJob(scheduleExpression20Minutes, main); // change to scheduleExpressionMinute for testing

job.start();
