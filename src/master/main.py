from master.setup import redis_connection, setup_logging, QUEUE_CONFIG
from master import helper
import logging
from master.helper import enqueue_random_jobs
from master.crawler.valid_countries_crawler import store_semrush_country_links
from master.crawler.top_ranked_urls_crawler import crawl_and_enqueue_jobs

logger = setup_logging("MASTER.main")

def main():
    """
    Entry point for the master node orchestration process.

    This function initializes the master workflow by verifying Redis connectivity
    and coordinating crawler operations. It first attempts to retrieve and store
    Semrush country links, logging the output location or any failures encountered.
    It then crawls top-ranked URLs and enqueues generated jobs into the configured
    Redis stream for worker consumption.

    All major steps are wrapped in exception handling to ensure that failures are
    logged clearly without causing silent crashes. If Redis is unreachable, the
    master node logs the error and terminates gracefully.
    """

    logger.info("Starting Master Node")
    try:
        helper.try_ping_redis(redis_connection)
        logger.info("Redis is reachable")

        #enqueue_random_jobs(redis_connection, QUEUE_CONFIG['stream_name'], logger)
        try:
            output_path = store_semrush_country_links()
            logger.info(f"Semrush country links saved to: {output_path}") 
        except Exception as e:
            logger.exception(f"Failed to store semrush country links: {e}")

        try:
            crawl_and_enqueue_jobs(
                connection=redis_connection,
                stream_name=QUEUE_CONFIG['stream_name'],
                logger=logger
            )
        except Exception as e:
            logger.exception(f"Failed to crawl and enqueue jobs: {e}")
        

        
    except Exception as e:
        logger.exception(f"Failed to reach Redis: {e}")
        return

    
if __name__ == "__main__":
    main()