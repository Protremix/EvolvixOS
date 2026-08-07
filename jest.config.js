module.exports = {
    preset: "ts-jest",
    testEnvironment: "node",
    testMatch: ["**/evm-tools/tests/**/*.test.ts"],
    moduleFileExtensions: ["ts", "js", "json"],
    transform: {
        "^.+\\.ts$": ["ts-jest", { tsconfig: { esModuleInterop: true } }]
    }
};
