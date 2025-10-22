"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const api_1 = require("@atproto/api");
const dotenv = __importStar(require("dotenv"));
const cron_1 = require("cron");
const process = __importStar(require("process"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const output_json_1 = __importDefault(require("./output.json"));
dotenv.config();
// Create a Bluesky Agent
const agent = new api_1.BskyAgent({
    service: 'https://atproto.bront.rodeo',
});
const INDEX_FILE = path.join(__dirname, 'current_index.txt');
// Flatten all entries from all pages into a single array
const allEntries = output_json_1.default.flatMap(page => page.entries);
function getCurrentIndex() {
    try {
        if (fs.existsSync(INDEX_FILE)) {
            const content = fs.readFileSync(INDEX_FILE, 'utf-8');
            return parseInt(content.trim(), 10) || 0;
        }
    }
    catch (error) {
        console.error('Error reading index file:', error);
    }
    return 0;
}
function saveCurrentIndex(index) {
    try {
        fs.writeFileSync(INDEX_FILE, index.toString(), 'utf-8');
    }
    catch (error) {
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
    await agent.login({ identifier: process.env.BLUESKY_USERNAME, password: process.env.BLUESKY_PASSWORD });
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
const scheduleExpression20Minutes = '*/20 * * * *'; // Run once every 20 minutes for testing
const scheduleExpression = '0 */3 * * *'; // Run once every three hours in prod
const job = new cron_1.CronJob(scheduleExpression20Minutes, main); // change to scheduleExpressionMinute for testing
job.start();
