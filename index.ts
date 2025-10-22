import { BskyAgent } from '@atproto/api';
import * as dotenv from 'dotenv';
import { CronJob } from 'cron';
import * as process from 'process';
import { readFileSync } from 'fs';

dotenv.config();

// Create a Bluesky Agent 
const agent = new BskyAgent({
    service: 'https://atproto.bront.rodeo',
  })


async function main() {
    let file = readFileSync('stirner.txt', 'utf8') 
    let stirner = file.toString()
    let lines = stirner.split(/\n\s*\n/);
    let haiku = lines[Math.floor(Math.random() * lines.length)];
    await agent.login({ identifier: process.env.BLUESKY_USERNAME!, password: process.env.BLUESKY_PASSWORD!})
    await agent.post({
        text: haiku
    });
    console.log("Just posted haiku", haiku)
}

main();


// Run this on a cron job
const scheduleExpressionMinute = '* * * * *'; // Run once every minute for testing
const scheduleExpression = '0 */3 * * *'; // Run once every three hours in prod

const job = new CronJob(scheduleExpression, main); // change to scheduleExpressionMinute for testing

job.start();
